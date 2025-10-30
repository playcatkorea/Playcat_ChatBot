"""
Playcat Chatbot API - Modular Architecture
고양이 행동풍부화 전문 상담 챗봇 시스템

작성자: Claude Code
버전: 2.0.0 (Modular)
날짜: 2025-01-XX
"""
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Configuration
from config.settings import get_settings

# Utils
from utils.logger import setup_logger
from utils.error_handler import handle_api_error

# Database
from database.connection import init_db

# Routers
from routers import chat, consultation, image, products

# Settings
settings = get_settings()

# Logger
logger = setup_logger("playcat_chatbot")


# ==================== Application Lifecycle ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트 처리"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"AI Model: {'Gemini' if settings.USE_GEMINI else 'Anthropic'}")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# ==================== FastAPI App Creation ====================

app = FastAPI(
    title=settings.APP_NAME,
    description="고양이 행동풍부화 상담 챗봇 (모듈화 아키텍처)",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)


# ==================== Middleware ====================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Error Handlers ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러"""
    return await handle_api_error(request, exc)


# ==================== Static Files ====================

# Static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================== Include Routers ====================

# Chat endpoints
app.include_router(chat.router)

# Consultation endpoints
app.include_router(consultation.router)

# Image upload/processing endpoints
app.include_router(image.router)

# Product catalog endpoints
app.include_router(products.router)


# ==================== Root Endpoints ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """루트 페이지 - 챗봇 UI"""
    return FileResponse("static/index.html")


@app.get("/api")
async def api_root():
    """API 정보"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "ai_model": "Gemini" if settings.USE_GEMINI else "Anthropic",
        "endpoints": {
            "chat": "/api/chat",
            "consultation": "/api/consultation",
            "image": "/api/image",
            "products": "/api/products",
            "health": "/api/health"
        },
        "documentation": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """헬스 체크 (모니터링용)"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENV
    }


# ==================== Application Entry Point ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
