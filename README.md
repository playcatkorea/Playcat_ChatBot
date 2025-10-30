# Playcat ChatBot - 고양이 행동풍부화 상담 챗봇

> 국내 유일 고양이 행동풍부화 전문 플레이캣의 AI 자동 상담 챗봇 시스템

## 프로젝트 개요

고양이 행동풍부화 가구 제작 업체 플레이캣의 자동 상담 챗봇 시스템입니다.
고객의 고양이 정보와 설치 공간 정보를 수집하여 AI가 최적의 제품 배치를 추천하고,
실내 사진에 제품을 합성한 이미지와 견적서를 자동으로 생성합니다.

## 주요 기능

### 🤖 AI 상담 챗봇
- Ollama 기반 한국어 LLM 사용 (qwen2.5, llama3.2)
- 고양이 행동풍부화 전문 지식 학습
- 자연스러운 대화형 상담 진행

### 📋 상담 유형 분기
1. **정밀 견적**: 고양이 상태와 환경을 점검받아 근본적인 문제 해결
2. **대략 가격**: 대략적인 가격 문의
3. **기타 문의**: 일반 문의사항

### 🖼️ AI 이미지 합성
- 고객 실내 사진에 제품 자동 배치
- PIL/OpenCV를 사용한 2D 합성
- 추후 ComfyUI + LoRA로 고도화 예정

### 📄 자동 견적서 생성
- PDF 형식 견적서 자동 생성
- 제품 구성, 가격, 설치 일정 포함
- 한글 폰트 지원

### 🔗 다중 채널 지원
- 웹 인터페이스
- 카카오톡 연동 (예정)
- 인스타그램 DM 연동 (예정)

## 기술 스택

| 구분 | 기술 |
|------|------|
| **LLM** | Ollama (qwen2.5, llama3.2) |
| **백엔드** | FastAPI, Python 3.9+ |
| **이미지 처리** | PIL, OpenCV |
| **데이터베이스** | SQLite, SQLAlchemy |
| **견적서 생성** | ReportLab |
| **프론트엔드** | HTML, CSS, JavaScript |

## 프로젝트 구조

```
Playcat_ChatBot/
├── chatbot/                    # 챗봇 로직
│   ├── ollama_client.py       # Ollama LLM 클라이언트
│   └── conversation_manager.py # 대화 흐름 관리
├── database/                   # DB 모델 및 연결
│   ├── models.py              # SQLAlchemy 모델
│   └── connection.py          # DB 연결 설정
├── services/                   # 비즈니스 로직
│   ├── image_composer.py      # 이미지 합성
│   └── quote_generator.py     # 견적서 생성
├── data/                       # 상담 데이터
│   ├── consultation_flow.json # 상담 흐름 정의
│   └── products.json          # 제품 정보 및 가격
├── static/                     # 정적 파일
│   ├── index.html             # 웹 UI
│   ├── uploads/               # 업로드 이미지
│   ├── composites/            # 합성 이미지
│   ├── quotes/                # 생성된 견적서
│   └── images/products/       # 제품 이미지
├── main.py                     # FastAPI 메인 앱
├── requirements.txt            # Python 패키지
├── SETUP.md                    # 설치 가이드
├── start.bat                   # Windows 시작 스크립트
└── start.sh                    # Linux/Mac 시작 스크립트
```

## 빠른 시작

### 1. 사전 요구사항
- Python 3.9 이상
- [Ollama](https://ollama.com) 설치

### 2. Ollama 모델 다운로드
```bash
ollama pull qwen2.5:latest
```

### 3. 가상환경 생성 및 패키지 설치
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 4. 서버 실행

#### Windows
```bash
start.bat
```

#### Linux/Mac
```bash
chmod +x start.sh
./start.sh
```

#### 또는 직접 실행
```bash
python main.py
```

### 5. 웹 접속
- **챗봇 UI**: http://localhost:8000/static/index.html
- **API 문서**: http://localhost:8000/docs
- **헬스 체크**: http://localhost:8000/api/health

## API 엔드포인트

### 챗봇
- `POST /api/chat/start` - 채팅 시작
- `POST /api/chat/message` - 메시지 전송
- `GET /api/chat/session/{session_id}` - 세션 조회

### 상담
- `POST /api/consultation/submit` - 상담 정보 제출

### 이미지
- `POST /api/image/upload` - 이미지 업로드
- `POST /api/image/composite` - 이미지 합성

### 견적서
- `POST /api/quote/generate` - 견적서 생성
- `GET /api/quote/download/{filename}` - 견적서 다운로드

### 기타
- `GET /api/products` - 제품 목록 조회
- `GET /api/health` - 헬스 체크

자세한 API 문서는 http://localhost:8000/docs 에서 확인하세요.

## 제품 이미지 준비

이미지 합성 기능을 사용하려면 투명 배경(PNG) 제품 이미지가 필요합니다:

```
static/images/products/
├── wall_walker_30.png
├── wall_walker_40.png
├── ceiling_walker_60.png
├── ceiling_walker_80.png
├── rest_spot_circle.png
├── rest_spot_square.png
├── scratcher_tower_120.png
├── scratcher_tower_180.png
├── cat_house_cube.png
└── transparent_bridge.png
```

배경 제거 도구: [remove.bg](https://remove.bg) 또는 `rembg` 라이브러리 사용

## 로드맵

### Phase 1: 기본 챗봇 ✅ (완료)
- [x] Ollama 연동
- [x] 대화 흐름 관리
- [x] 간단한 이미지 합성 (PIL/OpenCV)
- [x] 견적서 생성 (PDF)
- [x] 웹 인터페이스

### Phase 2: AI 이미지/영상 생성 ✅ (설계 완료)
- [x] 시스템 설계 ([docs/PHASE2_DESIGN.md](docs/PHASE2_DESIGN.md))
- [x] ComfyUI 워크플로우 작성
- [x] Qwen Image Edit 통합 (사진 정면 변환)
- [x] 제품 합성 (ControlNet + LoRA)
- [x] 고양이 놀이 장면 합성 (IP-Adapter)
- [x] 5초 동영상 생성 (AnimateDiff)
- [x] Python 통합 코드 작성
- [x] 설치 가이드 ([docs/PHASE2_INSTALL.md](docs/PHASE2_INSTALL.md))

**구현 예정:**
- [ ] GPU 서버 준비
- [ ] 제품 이미지 수집 (20-50장/제품)
- [ ] LoRA 모델 학습
- [ ] 실제 환경 테스트

### Phase 3: 채널 통합 (진행 예정)
- [ ] 카카오톡 챗봇 연동
- [ ] 인스타그램 DM 자동 응답
- [ ] 이메일 알림 시스템
- [ ] 관리자 대시보드

## 설정 커스터마이징

### 상담 흐름 수정
[data/consultation_flow.json](data/consultation_flow.json) 파일을 수정하여 대화 흐름 변경

### 제품 정보 수정
[data/products.json](data/products.json) 파일을 수정하여 제품 및 가격 변경

### AI 프롬프트 수정
[chatbot/ollama_client.py](chatbot/ollama_client.py) 파일의 `system_prompt` 수정

## 문제 해결

자세한 문제 해결 방법은 [SETUP.md](SETUP.md) 참조

### 자주 발생하는 문제

**Ollama 연결 오류**
```bash
# Ollama 서버 시작
ollama serve
```

**한글 폰트 오류 (견적서)**
- Windows: 자동으로 malgun.ttf 사용
- Linux: 나눔고딕 설치 필요

**데이터베이스 오류**
```bash
# 데이터베이스 재생성
rm playcat.db
python database/connection.py
```

## 라이선스

이 프로젝트는 플레이캣(PLAYCAT)의 내부 프로젝트입니다.

## 연락처

- **회사**: 플레이캣 (PLAYCAT)
- **전화**: 1522-5092 / 010-5676-8282
- **이메일**: thebloomkr@naver.com
- **웹사이트**: https://www.playcat.kr
- **인스타그램**: [@playcat.kr](https://www.instagram.com/playcat.kr)
