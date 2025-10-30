"""
Centralized Logging System
구조화된 로깅 유틸리티
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from config.settings import get_settings

# 로그 디렉토리 생성
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(
    name: str = "playcat_chatbot",
    log_file: str = None,
    level: str = None
) -> logging.Logger:
    """
    로거 설정 및 생성
    
    Args:
        name: 로거 이름
        log_file: 로그 파일 경로 (None이면 날짜 기반 자동 생성)
        level: 로그 레벨 (None이면 설정에서 가져옴)
    
    Returns:
        설정된 Logger 인스턴스
    """
    settings = get_settings()
    
    # 로거 생성
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 있으면 재사용
    if logger.handlers:
        return logger
    
    # 로그 레벨 설정
    log_level = level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 포맷터 생성
    formatter = logging.Formatter(
        settings.LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (프로덕션 환경)
    if settings.ENV == "production":
        if log_file is None:
            log_file = f"playcat_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(
            LOG_DIR / log_file,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 에러 전용 파일 핸들러
    error_file_handler = logging.FileHandler(
        LOG_DIR / f"error_{datetime.now().strftime('%Y%m%d')}.log",
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    logger.addHandler(error_file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    기존 로거 가져오기 또는 새로 생성
    
    Args:
        name: 로거 이름 (None이면 루트 로거)
    
    Returns:
        Logger 인스턴스
    """
    if name is None:
        name = "playcat_chatbot"
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        return setup_logger(name)
    
    return logger
