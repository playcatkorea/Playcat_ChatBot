from typing import Dict, List, Optional
import json
import os
from pathlib import Path

# Gemini 우선, Ollama fallback
USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"

if USE_GEMINI:
    try:
        from chatbot.gemini_client import gemini_client as ai_client
        print("[OK] Using Gemini API")
    except Exception as e:
        print(f"[WARN] Gemini failed, falling back to Ollama: {e}")
        from chatbot.ollama_client import ollama_client as ai_client
else:
    from chatbot.ollama_client import ollama_client as ai_client
    print("[OK] Using Ollama")

from services.comfyui_client import comfyui_client


class ConversationManager:
    """대화 흐름 관리"""

    def __init__(self):
        self.flow_data = self._load_flow_data()
        self.sessions: Dict[str, Dict] = {}

    def _load_flow_data(self) -> Dict:
        """상담 흐름 데이터 로드"""
        flow_path = Path(__file__).parent.parent / "data" / "consultation_flow.json"
        with open(flow_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def start_session(self, session_id: str) -> Dict:
        """
        새 세션 시작

        Args:
            session_id: 세션 ID

        Returns:
            초기 메시지 및 옵션
        """
        self.sessions[session_id] = {
            "current_step": "greeting",
            "conversation_history": [],
            "collected_data": {},
            "consultation_type": None
        }

        return self._get_current_message(session_id)

    def _get_current_message(self, session_id: str) -> Dict:
        """현재 단계의 메시지 반환"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "세션을 찾을 수 없습니다."}

        current_step = session["current_step"]
        step_data = self.flow_data.get(current_step, {})

        response = {
            "step": current_step,
            "message": step_data.get("message", ""),
        }

        if "options" in step_data:
            response["options"] = step_data["options"]

        if "required_fields" in step_data:
            response["required_fields"] = step_data["required_fields"]

        if "cat_info_fields" in step_data:
            response["cat_info_fields"] = step_data["cat_info_fields"]

        if "additional_fields" in step_data:
            response["additional_fields"] = step_data["additional_fields"]

        return response

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        selected_option: Optional[str] = None
    ) -> Dict:
        """
        사용자 메시지 처리

        Args:
            session_id: 세션 ID
            user_message: 사용자 메시지
            selected_option: 선택한 옵션 ID

        Returns:
            응답 메시지
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "세션을 찾을 수 없습니다."}

        # 대화 기록 저장
        session["conversation_history"].append({
            "role": "user",
            "content": user_message
        })

        current_step = session["current_step"]

        # 옵션 선택 처리
        if selected_option:
            response = await self._handle_option_selection(
                session_id, selected_option
            )
        # 상담 양식 단계
        elif current_step in ["consultation_form", "simple_form"]:
            response = await self._handle_form_submission(
                session_id, user_message
            )
        # AI 대화
        else:
            response = await self._handle_ai_chat(session_id, user_message)

        # 응답 기록 저장
        if "message" in response:
            session["conversation_history"].append({
                "role": "assistant",
                "content": response["message"]
            })

        return response

    async def _handle_option_selection(
        self,
        session_id: str,
        option_id: str
    ) -> Dict:
        """옵션 선택 처리"""
        session = self.sessions[session_id]
        current_step = session["current_step"]
        step_data = self.flow_data.get(current_step, {})

        # 선택한 옵션 찾기
        selected = None
        for option in step_data.get("options", []):
            if option["id"] == option_id:
                selected = option
                break

        if not selected:
            return {"error": "유효하지 않은 옵션입니다."}

        # 상담 유형 저장
        if current_step == "greeting":
            session["consultation_type"] = option_id

        # 다음 단계로 이동
        next_step = selected.get("next")
        if next_step:
            session["current_step"] = next_step
            return self._get_current_message(session_id)

        return {"message": "옵션이 선택되었습니다."}

    async def _handle_form_submission(
        self,
        session_id: str,
        form_data: str
    ) -> Dict:
        """양식 제출 처리"""
        session = self.sessions[session_id]

        # form_data는 JSON 문자열로 가정
        try:
            data = json.loads(form_data)
            session["collected_data"].update(data)

            # 데이터 검증
            validation_result = self._validate_form_data(session)
            if not validation_result["valid"]:
                return {
                    "error": "필수 정보가 누락되었습니다.",
                    "missing_fields": validation_result["missing_fields"]
                }

            # AI 분석 수행
            if hasattr(ai_client, 'analyze_consultation_data'):
                analysis = await ai_client.analyze_consultation_data(
                    session["collected_data"]
                )
            else:
                # Gemini fallback: 간단한 분석
                analysis = {
                    "summary": "상담 데이터가 수집되었습니다.",
                    "recommendations": ["전문 상담사가 곧 연락드리겠습니다."]
                }

            # 상담 유형에 따라 비디오 생성 (정밀 견적인 경우)
            video_result = None
            if session.get("consultation_type") == "detailed_quote":
                video_result = await self._generate_cat_video(session_id)

            response = {
                "message": "상담 정보가 접수되었습니다. 분석 중입니다...",
                "analysis": analysis,
                "next_action": "generate_quote"
            }

            if video_result:
                response["video_generation"] = video_result

            return response

        except json.JSONDecodeError:
            return {"error": "잘못된 데이터 형식입니다."}

    async def _generate_cat_video(self, session_id: str) -> Optional[Dict]:
        """
        고양이 사진과 기대하는 활동을 기반으로 비디오 생성

        Args:
            session_id: 세션 ID

        Returns:
            비디오 생성 결과 또는 None
        """
        session = self.sessions.get(session_id)
        if not session:
            return None

        collected_data = session.get("collected_data", {})
        cats = collected_data.get("cats", [])

        # 고양이 사진과 기대 활동이 있는지 확인
        for idx, cat in enumerate(cats):
            cat_photo = cat.get("cat_photo")
            expected_activity = cat.get("expected_activity")

            # 둘 다 있으면 비디오 생성
            if cat_photo and expected_activity:
                try:
                    # 프롬프트 자동 생성
                    text_prompt = await self._generate_image_prompt(cat, collected_data)
                    video_prompt = await self._generate_video_prompt(expected_activity)
                    audio_prompt = await self._generate_audio_prompt(expected_activity)

                    # ComfyUI로 비디오 생성
                    result = await comfyui_client.generate_cat_video_with_audio(
                        text_prompt=text_prompt,
                        video_positive_prompt=video_prompt["positive"],
                        video_negative_prompt=video_prompt["negative"],
                        audio_prompt=audio_prompt["positive"],
                        audio_negative_prompt=audio_prompt["negative"],
                        video_duration=5.0  # 5초 비디오
                    )

                    return {
                        "status": "success",
                        "cat_index": idx,
                        "image_url": result.get("image"),
                        "video_url": result.get("video"),
                        "prompt_id": result.get("prompt_id")
                    }

                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"비디오 생성 실패: {str(e)}"
                    }

        return {
            "status": "skipped",
            "message": "고양이 사진 또는 기대하는 활동 정보가 없습니다."
        }

    async def _generate_image_prompt(self, cat_data: Dict, space_data: Dict) -> str:
        """고양이와 공간 데이터로 이미지 프롬프트 생성"""
        breed = cat_data.get("breed", "cat")
        age = cat_data.get("age", "")
        personality = cat_data.get("personality", "playful")
        product_color = space_data.get("product_color", "wood")

        # 색상 매핑
        color_map = {
            "wood": "natural wooden",
            "wood_transparent": "natural wooden with transparent",
            "white": "white painted",
            "white_transparent": "white with transparent"
        }
        color_desc = color_map.get(product_color, "wooden")

        prompt = f"A beautiful {breed} cat playing energetically with a modern {color_desc} cat tower. "
        prompt += f"The cat has a {personality} personality. "
        prompt += "Natural afternoon sunlight streams through a window, creating warm highlights. "
        prompt += "Modern minimalist interior with plants in the background. "
        prompt += "High quality product photography, professional lighting, 8k resolution, sharp focus."

        return prompt

    async def _generate_video_prompt(self, expected_activity: str) -> Dict:
        """기대하는 활동으로 비디오 프롬프트 생성"""
        # 간단한 키워드 추출 (실제로는 Ollama로 더 정교하게 생성 가능)
        keywords = []

        if "오르내리" in expected_activity or "올라" in expected_activity:
            keywords.append("climbing motion")
        if "점프" in expected_activity or "뛰어" in expected_activity:
            keywords.append("playful jumping")
        if "쉬" in expected_activity or "휴식" in expected_activity:
            keywords.append("relaxed resting")
        if "구경" in expected_activity or "보" in expected_activity:
            keywords.append("observing curiously")

        if not keywords:
            keywords = ["smooth cat movements", "playful behavior"]

        return {
            "positive": ", ".join(keywords) + ", natural cat motion, smooth animation",
            "negative": "static, no movement, blurry, distorted, choppy motion, glitchy, artificial"
        }

    async def _generate_audio_prompt(self, expected_activity: str) -> Dict:
        """기대하는 활동으로 오디오 프롬프트 생성"""
        sounds = []

        if "오르내리" in expected_activity or "올라" in expected_activity:
            sounds.append("soft paw tapping on wood")
        if "점프" in expected_activity:
            sounds.append("light landing sounds")
        if "구경" in expected_activity:
            sounds.append("gentle ambient sounds")

        sounds.append("occasional satisfied purr")
        sounds.append("playful meowing sounds")

        return {
            "positive": ", ".join(sounds),
            "negative": "harsh noise, distortion, static, crackling, robotic sounds, loud bangs"
        }

    def _validate_form_data(self, session: Dict) -> Dict:
        """양식 데이터 검증"""
        current_step = session["current_step"]
        step_data = self.flow_data.get(current_step, {})
        required_fields = step_data.get("required_fields", [])

        collected = session["collected_data"]
        missing = []

        for field in required_fields:
            field_id = field["id"]
            if field["validation"].startswith("required"):
                if field_id not in collected or not collected[field_id]:
                    missing.append(field_id)

        return {
            "valid": len(missing) == 0,
            "missing_fields": missing
        }

    async def _handle_ai_chat(
        self,
        session_id: str,
        user_message: str
    ) -> Dict:
        """AI 대화 처리"""
        session = self.sessions[session_id]

        # AI를 통한 응답 생성
        response_text = await ai_client.chat(
            message=user_message,
            chat_history=session["conversation_history"]
        )

        return {
            "message": response_text,
            "step": session["current_step"]
        }

    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """세션 데이터 조회"""
        return self.sessions.get(session_id)

    def clear_session(self, session_id: str):
        """세션 삭제"""
        if session_id in self.sessions:
            del self.sessions[session_id]


# 전역 인스턴스
conversation_manager = ConversationManager()
