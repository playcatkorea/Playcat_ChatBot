"""
Centralized Error Handling
API 에러 처리 유틸리티
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Union
import traceback
from .logger import get_logger

logger = get_logger(__name__)


async def handle_api_error(request: Request, exc: Exception) -> JSONResponse:
    """
    전역 API 에러 핸들러
    
    모든 예외를 잡아서 일관된 형식으로 응답
    """
    # HTTPException은 FastAPI가 기본 처리
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    # 일반 예외 처리
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        exc_info=True
    )
    
    # 디버그 모드에서는 상세 트레이스백 제공
    from config.settings import get_settings
    settings = get_settings()
    
    error_detail = {
        "error": True,
        "message": "Internal server error",
        "status_code": 500
    }
    
    if settings.DEBUG:
        error_detail["detail"] = str(exc)
        error_detail["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content=error_detail
    )


class APIError(Exception):
    """커스텀 API 에러"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """입력 검증 에러"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(APIError):
    """리소스를 찾을 수 없음"""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status_code=404)


class UnauthorizedError(APIError):
    """인증 실패"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class RateLimitError(APIError):
    """속도 제한 초과"""
    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, status_code=429)
