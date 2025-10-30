"""
컨텐츠 필터: 고양이 상담 관련 내용만 허용
고양이와 무관한 요청, JSON 파일, 악의적 요청 차단
"""

import re
from typing import Dict, Tuple
import json


class ContentFilter:
    """컨텐츠 필터링 클래스"""

    def __init__(self):
        # 허용된 키워드 (고양이 관련 + 상담 관련)
        self.allowed_keywords = [
            # 고양이 관련
            "고양이", "캣", "cat", "고냥이", "냥이", "냥", "묘", "meow",
            "플레이캣", "playcat", "pet", "펫", "반려동물", "반려묘",
            "행동풍부화", "캣타워", "캣워크", "캣휠", "캣폴",
            "발판", "스크래쳐", "터널", "해먹", "안전", "건강",
            "집사", "고양이집사",
            # 상담/문의 관련 (고양이 없어도 허용)
            "설치", "견적", "상담", "문의", "가격", "비용", "금액",
            "제품", "구매", "주문", "예약", "신청",
            "전문가", "컨설팅", "도움", "도와", "알려",
            "궁금", "질문", "여쭤", "물어"
        ]

        # 차단할 키워드 (악의적/무관한 요청)
        self.blocked_keywords = [
            "json", "file", "파일", "다운로드", "download",
            "hack", "해킹", "sql", "injection", "xss",
            "script", "<script>", "javascript:",
            "admin", "관리자", "password", "비밀번호",
            "개", "강아지", "dog", "puppy",  # 개 관련 (고양이 아님)
            "정치", "politics", "종교", "religion",
            "사기", "scam", "불법", "illegal"
        ]

        # 위험한 패턴 (정규식)
        self.dangerous_patterns = [
            r'<script.*?>.*?</script>',  # XSS
            r'\.\./',  # Path traversal
            r'(union|select|insert|delete|drop|update|exec|execute).*?(from|into|table)',  # SQL Injection
            r'eval\(',  # JavaScript eval
            r'\.json$',  # JSON 파일 요청
            r'\.txt$',  # 텍스트 파일 요청
            r'\.py$',  # Python 파일 요청
            r'\.js$',  # JavaScript 파일 요청
            r'\.sh$',  # Shell 스크립트
            r'\.exe$',  # 실행 파일
            r'\.bat$',  # Batch 파일
        ]

    def is_allowed(self, message: str, is_option_selected: bool = False) -> Tuple[bool, str]:
        """
        메시지가 허용되는지 확인

        Args:
            message: 사용자 메시지
            is_option_selected: 옵션 버튼을 클릭한 경우 True

        Returns:
            (허용 여부, 거부 이유)
        """

        # 1. 빈 메시지 (단, 옵션 선택인 경우는 허용)
        if not message or not message.strip():
            if is_option_selected:
                return True, ""  # 옵션 선택 시 빈 메시지 허용
            return False, "빈 메시지는 허용되지 않습니다."

        message_lower = message.lower()

        # 2. 차단 키워드 확인
        for blocked in self.blocked_keywords:
            if blocked.lower() in message_lower:
                return False, f"죄송합니다. 이 챗봇은 **고양이 행동풍부화 상담 전용**입니다. '{blocked}' 관련 문의는 처리할 수 없습니다."

        # 3. 위험한 패턴 확인
        for pattern in self.dangerous_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return False, "⚠️ 보안 위험이 감지되었습니다. 이 요청은 차단됩니다."

        # 4. 허용 키워드 확인 (너무 짧은 메시지는 제외)
        if len(message) > 10:
            has_allowed_keyword = any(keyword in message_lower for keyword in self.allowed_keywords)

            if not has_allowed_keyword:
                # 일반적인 인사말은 허용
                greetings = ["안녕", "hi", "hello", "헬로", "안뇽", "ㅎㅇ", "반가", "처음", "시작"]
                if not any(greeting in message_lower for greeting in greetings):
                    return False, (
                        "죄송합니다. 이 챗봇은 **고양이 행동풍부화 전문 상담**만 제공합니다.\n\n"
                        "다음 주제로 문의해 주세요:\n"
                        "• 고양이 행동풍부화 시설 (캣타워, 캣워크, 발판 등)\n"
                        "• 설치 견적 및 상담\n"
                        "• 고양이 행동 문제 상담\n"
                        "• 제품 추천\n\n"
                        "고양이와 무관한 문의는 처리할 수 없습니다. 🐱"
                    )

        # 5. 모든 검사 통과
        return True, ""

    def sanitize_input(self, message: str) -> str:
        """입력 메시지 정제 (위험한 문자 제거)"""

        # HTML 태그 제거
        message = re.sub(r'<[^>]+>', '', message)

        # 연속된 공백 정리
        message = re.sub(r'\s+', ' ', message)

        # 특수문자 제한 (일부만 허용)
        # message = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?~@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|]', '', message)

        return message.strip()

    def check_spam(self, message: str) -> Tuple[bool, str]:
        """
        스팸 메시지 확인

        Returns:
            (스팸 여부, 이유)
        """

        # 1. 너무 긴 메시지 (5000자 제한)
        if len(message) > 5000:
            return True, "메시지가 너무 깁니다. 5000자 이내로 작성해주세요."

        # 2. 동일 문자 반복 (도배)
        if re.search(r'(.)\1{20,}', message):
            return True, "반복된 문자가 너무 많습니다."

        # 3. URL 스팸
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message)
        if len(urls) > 3:
            return True, "URL이 너무 많습니다. 스팸으로 의심됩니다."

        # 4. 이메일 스팸
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if len(emails) > 2:
            return True, "이메일 주소가 너무 많습니다."

        return False, ""

    def filter_message(self, message: str, is_option_selected: bool = False) -> Dict[str, any]:
        """
        메시지 종합 필터링

        Args:
            message: 사용자 메시지
            is_option_selected: 옵션 버튼을 클릭한 경우 True

        Returns:
            {
                "allowed": bool,
                "message": str (정제된 메시지),
                "reason": str (거부 이유),
                "is_spam": bool
            }
        """

        # 1. 입력 정제
        sanitized = self.sanitize_input(message)

        # 2. 스팸 확인 (옵션 선택 시 스킵)
        if not is_option_selected:
            is_spam, spam_reason = self.check_spam(sanitized)
            if is_spam:
                return {
                    "allowed": False,
                    "message": sanitized,
                    "reason": spam_reason,
                    "is_spam": True
                }

        # 3. 컨텐츠 필터링
        allowed, reason = self.is_allowed(sanitized, is_option_selected)

        return {
            "allowed": allowed,
            "message": sanitized,
            "reason": reason,
            "is_spam": False
        }


# 싱글톤 인스턴스
content_filter = ContentFilter()
