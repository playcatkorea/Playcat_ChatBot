"""
Image API Router
이미지 업로드 및 합성 관련 엔드포인트 모듈
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import uuid

from services.image_composer import image_composer

# Router 생성
router = APIRouter(prefix="/api/image", tags=["image"])

# 업로드 디렉토리
UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ImageCompositeRequest(BaseModel):
    background_url: str
    product_ids: List[str]
    positions: List[dict]  # [{"x": 100, "y": 200, "scale": 1.0}, ...]


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    이미지 업로드
    
    - 사용자가 업로드한 공간 사진 저장
    - UUID 기반 고유 파일명 생성
    - 지원 형식: jpg, jpeg, png, webp
    """
    try:
        # 파일 확장자 검증
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {allowed_extensions}"
            )
        
        # 고유 파일명 생성
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "success": True,
            "filename": unique_filename,
            "url": f"/static/uploads/{unique_filename}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/composite")
async def create_composite_image(request: ImageCompositeRequest):
    """
    이미지 합성
    
    - 배경 이미지에 제품 이미지 합성
    - 사용자가 선택한 위치와 스케일로 배치
    - AI 기반 자연스러운 합성
    """
    try:
        result = await image_composer.compose_image(
            background_url=request.background_url,
            product_ids=request.product_ids,
            positions=request.positions
        )
        
        if result.get("success"):
            return {
                "success": True,
                "composite_url": result.get("composite_url"),
                "message": "Image composition completed"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Composition failed")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Composition error: {str(e)}")
