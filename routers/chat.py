"""
Chat API Router
채팅 관련 엔드포인트 모듈
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from collections import defaultdict
import time

from chatbot.conversation_manager import conversation_manager
from chatbot.content_filter import content_filter
from services.kakao_notifier import get_kakao_notifier

# Router 생성
router = APIRouter(prefix="/api/chat", tags=["chat"])

# 중복 요청 방지
active_requests = defaultdict(lambda: {"count": 0, "last_time": 0})


class ChatStartRequest(BaseModel):
    session_id: Optional[str] = None
    language: Optional[str] = "ko"


class ChatMessage(BaseModel):
    session_id: str
    message: str
    selected_option: Optional[str] = None
    language: Optional[str] = "ko"


@router.post("/start")
async def start_chat(request: Request):
    """
    채팅 세션 시작

    초기 인사 및 옵션 제공
    """
    try:
        import uuid
        session_id = str(uuid.uuid4())
        session_data = conversation_manager.start_session(session_id)

        return {
            "session_id": session_id,
            "message": session_data.get("message"),
            "options": session_data.get("options", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message")
async def send_message(chat_message: ChatMessage, request: Request):
    """
    채팅 메시지 전송 및 응답 받기

    DDoS 방어: 같은 세션에서 동시 요청 방지
    """
    session_id = chat_message.session_id
    current_time = time.time()

    # 중복 요청 체크
    session_data = active_requests[session_id]
    if session_data["count"] > 0:
        if current_time - session_data["last_time"] < 1.0:
            raise HTTPException(
                status_code=429,
                detail="Too many simultaneous requests. Please wait."
            )

    try:
        # 요청 카운터 증가
        active_requests[session_id]["count"] += 1
        active_requests[session_id]["last_time"] = current_time

        # 컨텐츠 필터링
        is_safe, filtered_message = content_filter.filter(chat_message.message)
        if not is_safe:
            return {
                "response": "부적절한 내용이 감지되었습니다. 다시 입력해주세요.",
                "options": []
            }

        # 대화 처리 (기존 API 사용)
        response = await conversation_manager.process_message(
            session_id=session_id,
            user_message=filtered_message,
            selected_option=chat_message.selected_option
        )

        # 카카오톡 알림 전송 (비동기, 실패해도 응답에 영향 없음)
        try:
            kakao_notifier = get_kakao_notifier()
            await kakao_notifier.send_consultation_alert(
                session_id=session_id,
                user_message=filtered_message,
                bot_response=response.get("message", ""),
                context={
                    "intent": "chat",
                    "product_name": "-"
                }
            )
        except Exception as notification_error:
            print(f"[WARN] 카카오톡 알림 실패: {notification_error}")

        return {
            "response": response.get("message"),
            "options": response.get("options", [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        # 요청 카운터 감소
        active_requests[session_id]["count"] -= 1


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """세션 정보 조회"""
    try:
        session = conversation_manager.get_session_data(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    conversation_manager.clear_session(session_id)
    return {"message": "Session cleared"}
