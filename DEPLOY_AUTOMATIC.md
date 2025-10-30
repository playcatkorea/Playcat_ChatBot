# 🚀 자동 배포 가이드

## 📋 배포 준비 완료!

모든 코드가 Git에 커밋되었으며, 배포 준비가 완료되었습니다.

---

## ⚡ 빠른 배포 (5분)

### 1단계: GitHub 저장소 생성

1. **GitHub 접속**: https://github.com/new
2. **저장소 이름**: `Playcat_ChatBot`
3. **공개 설정**: Public (또는 Private)
4. **README 추가 안함** (이미 있음)
5. **Create repository** 클릭

### 2단계: 코드 푸시

GitHub에서 표시된 URL을 복사한 후 아래 명령어 실행:

```bash
cd c:\Users\playc\Project\Playcat_ChatBot

# GitHub 저장소 연결 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/Playcat_ChatBot.git

# 코드 푸시
git push -u origin main
```

**또는 PowerShell에서:**

```powershell
cd c:\Users\playc\Project\Playcat_ChatBot
git remote add origin https://github.com/YOUR_USERNAME/Playcat_ChatBot.git
git push -u origin main
```

### 3단계: Render.com 자동 배포

1. **Render 접속**: https://render.com/
2. **Sign Up** (GitHub 계정으로 로그인)
3. **New** → **Web Service** 클릭
4. **Connect a repository** → `Playcat_ChatBot` 선택
5. 설정 확인:
   - **Name**: `playcat-chatbot-api`
   - **Region**: `Singapore`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

6. **Environment Variables** 추가:
   ```
   USE_GEMINI=true
   GEMINI_API_KEY=AIzaSyByspltgfRno_NisFdYIFZ89HCoaZdokNU
   ```

7. **Create Web Service** 클릭

8. 배포 시작! (5-10분 소요)

---

## 🎯 배포 완료 후 확인

배포가 완료되면 다음 URL로 접속:

- **챗봇 메인**: `https://playcat-chatbot-api.onrender.com`
- **API 문서**: `https://playcat-chatbot-api.onrender.com/docs`
- **헬스 체크**: `https://playcat-chatbot-api.onrender.com/api/health`

---

## 📦 포함된 기능

✅ Gemini AI 2.5 Flash  
✅ 모듈화된 아키텍처  
✅ 카카오톡 알림 준비  
✅ 다크 모드 UI  
✅ 자동 로깅 시스템  
✅ 제품 지식 기반  

---

## 🔄 자동 재배포

코드를 수정하고 GitHub에 푸시하면 Render가 자동으로 재배포합니다:

```bash
git add .
git commit -m "업데이트 내용"
git push
```

---

## 💡 문제 해결

### 배포 실패 시

1. Render 대시보드에서 **Logs** 확인
2. 환경 변수 재확인
3. `render.yaml` 파일 확인

### 무료 플랜 슬립 모드

- 15분 미사용 시 자동 슬립
- 첫 접속 시 10-30초 소요
- Keep-alive 설정은 `.github/workflows/keep-alive.yml` 참조

---

**배포 완료되면 챗봇을 전 세계에서 사용할 수 있습니다! 🎉**
