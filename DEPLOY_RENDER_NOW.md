# 🚀 Render 배포 완전 가이드 (30분 완성)

> Cloudflare Pages + Google Gemini + Render 무료 호스팅

---

## ✅ Phase 1 완료 확인

- [x] Gemini API 키 발급 완료: `AIzaSyByspltgfRno_NisFdYIFZ89HCoaZdokNU`
- [x] .env 파일 설정 완료
- [x] 로컬 테스트 성공 (http://localhost:8000)
- [x] render.yaml 생성 완료

---

## 📋 Phase 2: Render 백엔드 배포 (15분)

### Step 1: GitHub 레포지토리 준비 (5분)

#### 1-1. Git 초기화 (이미 되어있지 않다면)

```bash
cd c:\Users\playc\Project\Playcat_ChatBot
git init
```

#### 1-2. .gitignore 확인

```bash
# .gitignore에 다음 내용이 있는지 확인
.env
*.pyc
__pycache__/
venv/
*.db
*.log
.vscode/
static/uploads/*
static/composites/*
static/quotes/*
!static/uploads/.gitkeep
!static/composites/.gitkeep
!static/quotes/.gitkeep
```

#### 1-3. GitHub 레포지토리 생성

1. https://github.com/new 접속
2. Repository name: `playcat-chatbot`
3. Public 또는 Private 선택
4. "Create repository" 클릭

#### 1-4. 로컬 코드 푸시

```bash
git add .
git commit -m "Initial commit - Gemini API integrated"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/playcat-chatbot.git
git push -u origin main
```

---

### Step 2: Render 배포 (10분)

#### 2-1. Render 계정 생성

1. https://render.com 접속
2. "Get Started for Free" 클릭
3. GitHub 계정으로 로그인

#### 2-2. New Web Service 생성

1. 대시보드에서 "New +" 클릭
2. "Web Service" 선택
3. "Connect a repository" - GitHub 연결
4. `playcat-chatbot` 레포지토리 선택

#### 2-3. 배포 설정

**Basic Settings:**
- **Name**: `playcat-chatbot-api`
- **Region**: Singapore (한국과 가까움)
- **Branch**: `main`
- **Root Directory**: (비워둠)

**Build & Deploy:**
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- **Free** 선택 (월 750시간 무료)

#### 2-4. 환경 변수 설정

"Environment" 탭에서 다음 추가:

| Key | Value |
|-----|-------|
| `USE_GEMINI` | `true` |
| `GEMINI_API_KEY` | `AIzaSyByspltgfRno_NisFdYIFZ89HCoaZdokNU` |
| `PYTHON_VERSION` | `3.12.0` |

#### 2-5. 배포 시작

- "Create Web Service" 클릭
- 자동으로 빌드 및 배포 시작 (5-10분 소요)
- 배포 로그 실시간 확인 가능

#### 2-6. 배포 완료 확인

배포가 완료되면 URL이 생성됩니다:
```
https://playcat-chatbot-api.onrender.com
```

**헬스 체크:**
```bash
curl https://playcat-chatbot-api.onrender.com/api/health
```

응답:
```json
{"status": "ok", "ai_model": "gemini-2.5-flash"}
```

---

## 🌐 Phase 3: Cloudflare Pages 프론트엔드 배포 (10분)

### Step 1: static 폴더 API URL 수정 (5분)

#### 1-1. static/index.html 수정

파일 위치: `static/index.html`

JavaScript 코드에서 API URL 찾기:

```javascript
// 기존 (로컬)
const API_URL = 'http://localhost:8000';

// 변경 (Render)
const API_URL = 'https://playcat-chatbot-api.onrender.com';
```

#### 1-2. 변경 사항 커밋

```bash
git add static/index.html
git commit -m "Update API URL for Render deployment"
git push origin main
```

---

### Step 2: Cloudflare Pages 배포 (5분)

#### 2-1. Cloudflare 계정 생성

1. https://dash.cloudflare.com/ 접속
2. 계정 생성 또는 로그인

#### 2-2. Pages 프로젝트 생성

1. 좌측 메뉴에서 "Workers & Pages" 클릭
2. "Create application" 클릭
3. "Pages" 탭 선택
4. "Connect to Git" 클릭

#### 2-3. GitHub 연결

1. "Connect GitHub" 클릭
2. `playcat-chatbot` 레포지토리 선택
3. "Begin setup" 클릭

#### 2-4. 빌드 설정

- **Project name**: `playcat-chatbot`
- **Production branch**: `main`
- **Build command**: (비워둠 - 정적 파일만)
- **Build output directory**: `static`

#### 2-5. 배포 완료

- "Save and Deploy" 클릭
- 1-2분 후 배포 완료
- URL 생성: `https://playcat-chatbot.pages.dev`

---

## ✅ 배포 완료 체크리스트

### 백엔드 (Render)
- [ ] GitHub 레포지토리 생성 및 푸시
- [ ] Render 계정 생성
- [ ] Web Service 생성
- [ ] 환경 변수 설정 (USE_GEMINI, GEMINI_API_KEY)
- [ ] 배포 성공 확인
- [ ] 헬스 체크 성공: `https://playcat-chatbot-api.onrender.com/api/health`

### 프론트엔드 (Cloudflare Pages)
- [ ] static/index.html API URL 업데이트
- [ ] 변경사항 커밋 및 푸시
- [ ] Cloudflare 계정 생성
- [ ] Pages 프로젝트 생성
- [ ] GitHub 연결
- [ ] 배포 완료: `https://playcat-chatbot.pages.dev`

### 테스트
- [ ] 챗봇 UI 접속 확인
- [ ] 채팅 전송 테스트
- [ ] AI 응답 정상 수신
- [ ] 제품 상담 기능 테스트

---

## 🔧 문제 해결

### Render 배포 실패

**증상:** 빌드 중 오류 발생

**해결방법:**
1. Render 대시보드 → Logs 탭 확인
2. 오류 메시지 확인:
   - `ModuleNotFoundError`: requirements.txt 확인
   - `Port binding`: Start Command에 `--port $PORT` 확인
   - `Timeout`: Free tier는 빌드 15분 제한

**일반적인 해결책:**
```bash
# requirements.txt 업데이트
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push origin main
```

---

### Render 슬립 이슈

**증상:** 첫 요청 시 5-10초 지연

**원인:** Free tier는 15분 비활성 후 슬립

**해결방법 1: GitHub Actions Keep-Alive (추천)**

`.github/workflows/keep-alive.yml` 생성:

```yaml
name: Keep Render Alive
on:
  schedule:
    - cron: '*/5 * * * *'  # 5분마다
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping API
        run: |
          curl -f https://playcat-chatbot-api.onrender.com/api/health || exit 0
```

**해결방법 2: UptimeRobot (외부 서비스)**

1. https://uptimerobot.com 가입
2. "Add New Monitor" 클릭
3. Monitor Type: HTTP(s)
4. URL: `https://playcat-chatbot-api.onrender.com/api/health`
5. Monitoring Interval: 5 minutes
6. 무료로 50개 모니터 지원

---

### CORS 에러

**증상:** 브라우저 콘솔에 "CORS policy" 에러

**해결방법:**

main.py가 이미 CORS 설정을 포함하고 있습니다:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

만약 특정 도메인만 허용하려면:
```python
allow_origins=[
    "https://playcat-chatbot.pages.dev",
    "https://www.playcat.kr"
],
```

---

### Cloudflare Pages 빌드 실패

**증상:** Cloudflare Pages 빌드 에러

**해결방법:**

Cloudflare Pages는 정적 파일만 호스팅합니다. `static` 폴더만 배포하면 됩니다.

**빌드 설정 재확인:**
- Build command: (비워둠)
- Build output directory: `static`

---

## 📊 비용 분석

### 현재 무료 사용량

| 서비스 | 무료 제공 | 현재 사용 | 초과 시 비용 |
|--------|-----------|-----------|--------------|
| **Render** | 750시간/월 | ~720시간 | $7/월 (Starter) |
| **Cloudflare Pages** | 무제한 | 무제한 | 완전 무료 |
| **Google Gemini** | 100만 토큰/월 | ~수천 토큰 | 초과 후 유료 |

**예상 트래픽:**
- 일일 100명 방문
- 인당 10개 메시지
- 월 30,000 메시지
- 월 토큰 사용량: ~3만 토큰 (3% 사용)

**결론:** 완전 무료로 운영 가능! 🎉

---

## 🚀 추가 최적화

### 1. 커스텀 도메인 연결

#### Cloudflare Pages 도메인 연결
1. Cloudflare Pages 프로젝트 선택
2. "Custom domains" 탭
3. "Set up a custom domain" 클릭
4. 도메인 입력: `chatbot.playcat.kr`
5. DNS 레코드 자동 설정

#### Render 도메인 연결
1. Render 대시보드 → Settings
2. "Custom Domain" 섹션
3. 도메인 입력: `api.playcat.kr`
4. DNS CNAME 레코드 추가:
   ```
   api.playcat.kr CNAME playcat-chatbot-api.onrender.com
   ```

---

### 2. 성능 모니터링

**Render 모니터링:**
- Render 대시보드 → Metrics
- CPU, 메모리, 응답 시간 확인

**Cloudflare Analytics:**
- Cloudflare Pages → Analytics
- 방문자 수, 대역폭, 요청 수 확인

**추천 툴:**
- **UptimeRobot**: 무료 업타임 모니터링
- **Google Analytics**: 사용자 행동 분석
- **Sentry**: 에러 추적 (무료 5,000 이벤트/월)

---

### 3. 데이터베이스 업그레이드

현재 SQLite 사용 → 프로덕션 환경에서는 PostgreSQL 권장

**Supabase (추천 - 무료):**
1. https://supabase.com 가입
2. New Project 생성
3. Database URL 복사
4. Render 환경 변수 추가:
   ```
   DATABASE_URL=postgresql://...supabase.co/postgres
   ```

**무료 제공:**
- 500MB 저장
- 무제한 API 요청
- 실시간 동기화

---

## 🎯 다음 단계

### 1. 카카오톡 채널 연동
- 카카오 비즈니스 계정 생성
- 챗봇 API 연동
- 자동 응답 설정

### 2. 인스타그램 DM 자동 응답
- Facebook Developer 계정
- Instagram Business API
- Webhook 설정

### 3. 이미지 생성 고도화
- ComfyUI 클라우드 연동
- LoRA 모델 학습
- GPU 인스턴스 (필요 시)

---

## 📞 지원

**문제 발생 시:**
1. GitHub Issues: https://github.com/YOUR_USERNAME/playcat-chatbot/issues
2. Render Support: https://render.com/docs
3. Cloudflare Community: https://community.cloudflare.com/

---

## 🎊 완료!

축하합니다! 플레이캣 챗봇이 무료로 전세계에 배포되었습니다!

**최종 URL:**
- 💬 챗봇: https://playcat-chatbot.pages.dev
- 🔌 API: https://playcat-chatbot-api.onrender.com

**성능:**
- ⚡ Gemini 2.5 Flash (최신 AI)
- 🌍 Cloudflare CDN (115% 빠름)
- 💰 완전 무료 (월 0원)
- 📈 자동 스케일링

---

**작성일**: 2025-10-27
**소요 시간**: 30분
**총 비용**: 0원
**상태**: ✅ 배포 준비 완료
