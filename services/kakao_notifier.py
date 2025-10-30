"""
카카오톡 알림 서비스
상담 내용을 자동으로 카카오톡으로 전달하는 모듈
"""
import os
import json
import aiohttp
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class KakaoNotifier:
    """
    카카오톡 비즈니스 메시지 발송 서비스
    
    지원 방식:
    1. 카카오톡 비즈니스 API (추천)
    2. 카카오 알림톡 API
    3. Webhook 방식 (대체)
    """
    
    def __init__(self):
        self.api_key = os.getenv("KAKAO_API_KEY")
        self.rest_api_key = os.getenv("KAKAO_REST_API_KEY")
        self.admin_phone = os.getenv("KAKAO_ADMIN_PHONE")
        self.sender_key = os.getenv("KAKAO_SENDER_KEY")
        self.template_code = os.getenv("KAKAO_TEMPLATE_CODE", "default")
        
        # Webhook 대체 방식
        self.webhook_url = os.getenv("KAKAO_WEBHOOK_URL")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")  # 개발/테스트용
        
        self.enabled = bool(self.api_key or self.webhook_url or self.discord_webhook)
        
        if not self.enabled:
            logger.warning("카카오톡 알림이 비활성화되었습니다. 환경 변수를 설정하세요.")
    
    async def send_consultation_alert(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        상담 내용을 카카오톡으로 전송
        
        Args:
            session_id: 세션 ID
            user_message: 사용자 메시지
            bot_response: 봇 응답
            context: 추가 컨텍스트 (제품 정보, 의도 등)
        
        Returns:
            전송 성공 여부
        """
        if not self.enabled:
            logger.debug("카카오톡 알림이 비활성화되어 있습니다.")
            return False
        
        try:
            # 메시지 포맷팅
            message = self._format_consultation_message(
                session_id, user_message, bot_response, context
            )
            
            # 전송 방법 선택
            if self.api_key and self.admin_phone:
                return await self._send_via_kakao_api(message)
            elif self.webhook_url:
                return await self._send_via_webhook(message)
            elif self.discord_webhook:
                # 개발/테스트용 Discord webhook
                return await self._send_via_discord(message)
            else:
                logger.error("카카오톡 전송 방법이 설정되지 않았습니다.")
                return False
                
        except Exception as e:
            logger.error(f"카카오톡 알림 전송 실패: {e}", exc_info=True)
            return False
    
    def _format_consultation_message(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        context: Dict[str, Any]
    ) -> str:
        """상담 내용을 읽기 좋은 형식으로 포맷팅"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 컨텍스트에서 중요 정보 추출
        intent = context.get("intent", "알 수 없음")
        product = context.get("product_name", "-")
        
        message = f"""
[플레이캣 챗봇 상담]

⏰ 시간: {timestamp}
📝 세션: {session_id[:12]}...
🎯 의도: {intent}
📦 제품: {product}

👤 고객 문의:
{user_message[:200]}{"..." if len(user_message) > 200 else ""}

🤖 봇 응답:
{bot_response[:200]}{"..." if len(bot_response) > 200 else ""}

---
💡 전체 대화 내용은 관리자 대시보드에서 확인하세요.
        """.strip()
        
        return message
    
    async def _send_via_kakao_api(self, message: str) -> bool:
        """카카오톡 비즈니스 API를 통한 전송"""
        try:
            url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            template_object = {
                "object_type": "text",
                "text": message,
                "link": {
                    "web_url": "https://www.playcat.kr",
                    "mobile_web_url": "https://www.playcat.kr"
                }
            }
            
            data = {
                "template_object": json.dumps(template_object)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        logger.info("카카오톡 알림 전송 성공")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"카카오톡 API 오류 ({response.status}): {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"카카오톡 API 전송 실패: {e}")
            return False
    
    async def _send_via_webhook(self, message: str) -> bool:
        """일반 Webhook을 통한 전송"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status in [200, 201, 204]:
                        logger.info("Webhook 알림 전송 성공")
                        return True
                    else:
                        logger.error(f"Webhook 오류: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Webhook 전송 실패: {e}")
            return False
    
    async def _send_via_discord(self, message: str) -> bool:
        """개발/테스트용 Discord webhook 전송"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "content": f"```\n{message}\n```",
                    "username": "플레이캣 챗봇"
                }
                
                async with session.post(
                    self.discord_webhook,
                    json=payload
                ) as response:
                    if response.status in [200, 204]:
                        logger.info("Discord 알림 전송 성공 (테스트 모드)")
                        return True
                    else:
                        logger.error(f"Discord webhook 오류: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Discord webhook 전송 실패: {e}")
            return False
    
    async def send_quote_request_alert(
        self,
        user_info: Dict[str, str],
        quote_details: Dict[str, Any]
    ) -> bool:
        """견적 요청 알림 전송"""
        if not self.enabled:
            return False
        
        try:
            message = f"""
[플레이캣 견적 요청]

⏰ 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

👤 고객 정보:
- 이름: {user_info.get('name', '-')}
- 연락처: {user_info.get('phone', '-')}
- 이메일: {user_info.get('email', '-')}

📦 요청 내용:
- 제품: {quote_details.get('product_name', '-')}
- 수량: {quote_details.get('quantity', '-')}
- 메시지: {quote_details.get('message', '-')[:100]}

🔗 빠른 응답: https://www.playcat.kr/admin/quotes
            """.strip()
            
            # 동일한 전송 메커니즘 사용
            if self.api_key:
                return await self._send_via_kakao_api(message)
            elif self.webhook_url:
                return await self._send_via_webhook(message)
            elif self.discord_webhook:
                return await self._send_via_discord(message)
            
            return False
            
        except Exception as e:
            logger.error(f"견적 요청 알림 전송 실패: {e}")
            return False


# 싱글톤 인스턴스
_kakao_notifier = None


def get_kakao_notifier() -> KakaoNotifier:
    """KakaoNotifier 싱글톤 인스턴스 반환"""
    global _kakao_notifier
    if _kakao_notifier is None:
        _kakao_notifier = KakaoNotifier()
    return _kakao_notifier
