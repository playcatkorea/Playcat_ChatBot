"""
Application Settings
환경 변수 기반 설정 관리
"""
import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    애플리케이션 설정
    
    환경 변수 또는 .env 파일에서 자동 로드
    """
    
    # Application
    APP_NAME: str = "Playcat Chatbot API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENV: str = "production"  # development, production
    
    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    USE_GEMINI: bool = True
    
    # KakaoTalk Notifications
    KAKAO_API_KEY: Optional[str] = None
    KAKAO_REST_API_KEY: Optional[str] = None
    KAKAO_ADMIN_PHONE: Optional[str] = None
    KAKAO_SENDER_KEY: Optional[str] = None
    KAKAO_TEMPLATE_CODE: str = "default"
    KAKAO_WEBHOOK_URL: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./playcat_chatbot.db"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".webp"}
    UPLOAD_DIR: str = "static/uploads"
    
    # ComfyUI (이미지 생성)
    COMFYUI_SERVER_ADDRESS: str = "127.0.0.1:8188"
    COMFYUI_ENABLED: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    설정 싱글톤 반환
    
    lru_cache로 한 번만 로드
    """
    return Settings()
