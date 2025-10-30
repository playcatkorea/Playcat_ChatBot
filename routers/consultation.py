"""
Consultation API Router
상담 및 견적 관련 엔드포인트 모듈
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import Consultation, Installation, Cat
from services.kakao_notifier import get_kakao_notifier
from services.quote_generator import quote_generator

# Router 생성
router = APIRouter(prefix="/api/consultation", tags=["consultation"])


class ConsultationData(BaseModel):
    session_id: str
    installation_region: str
    installation_location: str
    cat_count: int
    width: float
    height: float
    ceiling_height: float
    product_color: str
    cats: List[Dict]
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


@router.post("/submit")
async def submit_consultation(
    consultation_data: ConsultationData,
    db: AsyncSession = Depends(get_db)
):
    """
    상담 정보 제출 및 저장
    
    - 설치 정보
    - 고양이 정보
    - 연락처 정보
    - 데이터베이스 저장
    - 카카오톡 알림 전송
    """
    try:
        # Installation 레코드 생성
        installation = Installation(
            session_id=consultation_data.session_id,
            installation_region=consultation_data.installation_region,
            installation_location=consultation_data.installation_location,
            cat_count=consultation_data.cat_count,
            width=consultation_data.width,
            height=consultation_data.height,
            ceiling_height=consultation_data.ceiling_height,
            product_color=consultation_data.product_color
        )
        db.add(installation)
        await db.flush()  # ID 생성을 위해 flush
        
        # Cat 레코드 생성
        for cat_data in consultation_data.cats:
            cat = Cat(
                installation_id=installation.id,
                name=cat_data.get("name"),
                age=cat_data.get("age"),
                weight=cat_data.get("weight"),
                personality=cat_data.get("personality"),
                health_issues=cat_data.get("health_issues")
            )
            db.add(cat)
        
        # Consultation 레코드 생성
        consultation = Consultation(
            session_id=consultation_data.session_id,
            installation_id=installation.id,
            contact_name=consultation_data.contact_name,
            contact_phone=consultation_data.contact_phone,
            contact_email=consultation_data.contact_email,
            status="pending"
        )
        db.add(consultation)
        
        await db.commit()
        
        # 카카오톡 견적 요청 알림
        if consultation_data.contact_name or consultation_data.contact_phone:
            try:
                kakao_notifier = get_kakao_notifier()
                await kakao_notifier.send_quote_request_alert(
                    user_info={
                        "name": consultation_data.contact_name,
                        "phone": consultation_data.contact_phone,
                        "email": consultation_data.contact_email
                    },
                    quote_details={
                        "product_name": f"캣워커 설치 ({consultation_data.installation_location})",
                        "quantity": f"{consultation_data.cat_count}마리",
                        "message": f"공간: {consultation_data.width}x{consultation_data.height}x{consultation_data.ceiling_height}cm"
                    }
                )
            except Exception as notification_error:
                print(f"[WARN] 카카오톡 알림 실패: {notification_error}")
        
        return {
            "success": True,
            "message": "상담 신청이 완료되었습니다!",
            "consultation_id": consultation.id
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{consultation_id}")
async def get_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """특정 상담 정보 조회"""
    try:
        consultation = await db.get(Consultation, consultation_id)
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        return {"consultation": consultation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_consultations_by_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """세션별 상담 내역 조회"""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(Consultation).where(Consultation.session_id == session_id)
        )
        consultations = result.scalars().all()
        
        return {"consultations": consultations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
