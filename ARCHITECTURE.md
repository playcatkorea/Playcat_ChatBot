# 플레이캣 챗봇 - 모듈화 아키텍처 문서

**버전**: 2.0.0 (Modular)  
**작성일**: 2025-01-XX  
**작성자**: Claude Code

---

## 개요

플레이캣 챗봇은 완전한 모듈화 아키텍처로 재구성되었습니다.

### 핵심 개선사항

1. **Frontend 모듈화**
   - CSS, JavaScript를 별도 파일로 분리
   - Class 기반 OOP 구조
   - 다크 모드 지원

2. **Backend 모듈화**
   - Router별 파일 분리 (chat, consultation, image, products)
   - 비즈니스 로직 Services 레이어
   - 중앙화된 설정 및 로깅

3. **KakaoTalk 알림 통합**
   - 상담 내용 자동 전송
   - 다중 전송 방식 지원 (API, Webhook, Discord)

4. **전문가급 코드 구조**
   - 의존성 주입 패턴
   - 에러 처리 표준화
   - 로깅 시스템 구축

---

## 프로젝트 구조

