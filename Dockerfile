# ==========================================
# Playcat Chatbot - Optimized for Cloud Run
# ==========================================

FROM python:3.11-slim

# 메타데이터
LABEL maintainer="playcat@example.com"
LABEL description="Playcat AI Chatbot - Google Cloud Run Optimized"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (최소화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p static/images static/videos

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV USE_GEMINI=true

# Cloud Run은 PORT 환경 변수 사용
EXPOSE 8080

# Health check (선택)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/health')"

# uvicorn 실행 (Cloud Run 최적화)
CMD exec uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --timeout-keep-alive 5
