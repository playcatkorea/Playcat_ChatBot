"""
Google Gemini API 클라이언트
무료 티어: 15 RPM (분당 요청), 1,500 RPD (일일 요청)
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
import google.generativeai as genai


class GeminiClient:
    """Google Gemini API를 사용한 AI 클라이언트"""

    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Args:
            model: 사용할 Gemini 모델
                  - gemini-2.5-flash (무료, 최신, 가장 빠름, 추천!)
                  - gemini-2.5-pro (고급, 더 강력)
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

        # Playcat 데이터 로드
        self.knowledge = self._load_knowledge()
        self.products = self._load_products()
        self.system_prompt = self._build_system_prompt()

    def _load_knowledge(self) -> Dict:
        """지식 베이스 로드"""
        try:
            knowledge_path = Path(__file__).parent.parent / "data" / "chatbot_knowledge.json"
            with open(knowledge_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load knowledge: {e}")
            return {}

    def _load_products(self) -> Dict:
        """제품 데이터 로드"""
        try:
            products_path = Path(__file__).parent.parent / "data" / "products_real.json"
            with open(products_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load products: {e}")
            return {}

    def _build_system_prompt(self) -> str:
        """시스템 프롬프트 구성"""
        brand_info = self.products.get("brand_info", {})
        products_list = []

        for product in self.products.get("products", [])[:10]:  # 상위 10개만
            products_list.append(
                f"- {product['name']}: {product['base_price']:,}원"
            )

        faq_list = []
        for faq in self.products.get("faq", []):
            faq_list.append(f"Q: {faq['question']}\nA: {faq['answer']}")

        return f"""당신은 플레이캣(PLAYCAT)의 고양이 행동풍부화 전문 상담사입니다.

=== 회사 정보 ===
- 브랜드: {brand_info.get('name', 'Playcat')}
- 철학: {brand_info.get('philosophy', '행동풍부화와 고양이의 행복은 정비례')}
- 특징: 타공 불필요한 안전한 설치 방식

=== 주요 제품 (상위 10개) ===
{chr(10).join(products_list)}

=== 설치 정보 ===
- 출장 설치비: 기본 100,000원 (지역별 추가)
- 배송비: 기본 6,000원 (제주 24,000원)

=== 자주 묻는 질문 ===
{chr(10).join(faq_list[:3])}

=== 상담 원칙 ===
1. 친절하고 전문적으로 답변
2. 고양이의 품종, 나이, 체중 고려
3. 안전을 최우선으로 강조
4. 구체적인 가격 정보 제공
5. 필요시 상세 견적 안내

반드시 한국어로 답변하세요.
"""

    async def chat(
        self,
        message: str,
        context: Optional[str] = None,
        chat_history: Optional[list] = None
    ) -> str:
        """
        채팅 메시지 처리

        Args:
            message: 사용자 메시지
            context: 추가 컨텍스트 (선택)
            chat_history: 대화 히스토리 (선택)

        Returns:
            AI 응답 메시지
        """
        try:
            # 전체 프롬프트 구성
            full_prompt = f"{self.system_prompt}\n\n"

            if context:
                full_prompt += f"=== 현재 상황 ===\n{context}\n\n"

            if chat_history:
                full_prompt += "=== 이전 대화 ===\n"
                for entry in chat_history[-5:]:  # 최근 5개만
                    full_prompt += f"사용자: {entry.get('user', '')}\n"
                    full_prompt += f"플레이캣: {entry.get('assistant', '')}\n"
                full_prompt += "\n"

            full_prompt += f"=== 현재 질문 ===\n사용자: {message}\n플레이캣:"

            # Gemini API 호출
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,  # 창의성 조절
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=1024,
                )
            )

            return response.text.strip()

        except Exception as e:
            error_msg = f"AI 응답 생성 중 오류 발생: {str(e)}"
            print(error_msg)
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    def get_product_info(self, product_id: str) -> Optional[Dict]:
        """특정 제품 정보 조회"""
        for product in self.products.get("products", []):
            if product.get("id") == product_id:
                return product
        return None

    def answer_faq(self, question: str) -> Optional[str]:
        """FAQ 검색"""
        for faq in self.products.get("faq", []):
            if question.lower() in faq["question"].lower():
                return faq["answer"]
        return None

    def get_breed_tips(self, breed: str) -> Optional[str]:
        """품종별 팁"""
        breed_tips = self.products.get("breed_specific_tips", {})
        return breed_tips.get(breed)


# 싱글톤 인스턴스 (환경 변수가 있을 때만 생성)
gemini_client = None
if os.getenv("GEMINI_API_KEY"):
    try:
        gemini_client = GeminiClient()
        print("[OK] Gemini API client initialized")
    except Exception as e:
        print(f"[WARN] Failed to initialize Gemini client: {e}")
