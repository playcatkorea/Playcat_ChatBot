@echo off
chcp 65001 > nul
echo ========================================
echo 플레이캣 챗봇 자동 배포 스크립트
echo ========================================
echo.

cd /d "c:\Users\playc\Project\Playcat_ChatBot"

echo [단계 1/3] GitHub 사용자명 입력
echo.
set /p GITHUB_USER="GitHub 사용자명을 입력하세요: "
echo.

echo [단계 2/3] Git 원격 저장소 설정...
git remote remove origin 2>nul
git remote add origin https://github.com/%GITHUB_USER%/Playcat_ChatBot.git
echo ✅ 원격 저장소 설정 완료
echo.

echo [단계 3/3] GitHub에 푸시 중...
echo.
git push -u origin main
echo.

if %ERRORLEVEL% EQU 0 (
    echo ========================================
    echo ✅ GitHub 푸시 성공!
    echo ========================================
    echo.
    echo 다음 단계:
    echo 1. https://render.com 접속
    echo 2. GitHub로 로그인
    echo 3. New Web Service 클릭
    echo 4. Playcat_ChatBot 저장소 선택
    echo 5. 환경 변수 추가:
    echo    - USE_GEMINI=true
    echo    - GEMINI_API_KEY=AIzaSyByspltgfRno_NisFdYIFZ89HCoaZdokNU
    echo 6. Create Web Service 클릭
    echo.
    echo 📖 자세한 가이드: DEPLOY_AUTOMATIC.md
    echo.
) else (
    echo ========================================
    echo ❌ 푸시 실패
    echo ========================================
    echo.
    echo GitHub에서 먼저 저장소를 생성해주세요:
    echo https://github.com/new
    echo.
    echo 저장소 이름: Playcat_ChatBot
    echo.
)

pause
