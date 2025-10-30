"""
플레이캣 전문 Ollama 클라이언트 (실제 데이터 기반)
"""
import ollama
from typing import List, Dict, Optional
import json
from pathlib import Path


class PlaycatOllamaClient:
    """플레이캣 전문 상담 AI 클라이언트"""

    def __init__(self, model: str = "qwen2.5:latest"):
        self.model = model
        self.knowledge = self._load_knowledge()
        self.products = self._load_products()
        self.system_prompt = self._build_system_prompt()

    def _load_knowledge(self) -> Dict:
        """상담 지식 베이스 로드"""
        knowledge_path = Path(__file__).parent.parent / "data" / "chatbot_knowledge.json"
        with open(knowledge_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_products(self) -> Dict:
        """제품 데이터 로드"""
        products_path = Path(__file__).parent.parent / "data" / "products_real.json"
        with open(products_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_system_prompt(self) -> str:
        """실제 데이터 기반 시스템 프롬프트 생성"""

        brand_info = self.products.get("brand_info", {})
        design_principles = self.products.get("design_principles", {})

        # 주요 제품 목록 생성
        products_list = []
        for product in self.products.get("products", [])[:10]:  # 처음 10개만
            products_list.append(
                f"- {product['name']}: {product['base_price']:,}원 ({product['description']})"
            )

        # FAQ 목록
        faq_list = []
        for faq in self.products.get("faq", [])[:5]:  # 처음 5개만
            faq_list.append(f"Q: {faq['question']}\nA: {faq['answer']}")

        return f"""당신은 플레이캣(PLAYCAT)의 고양이 행동풍부화 전문 상담사입니다.

=== 회사 정보 ===
- 브랜드: {brand_info.get('name', '플레이캣')}
- 철학: {brand_info.get('philosophy', '행동풍부화와 고양이의 행복은 정비례')}
- 특징: {brand_info.get('specialty', '동물행동학 기반')}
- 웹사이트: {brand_info.get('website', 'https://www.playcat.kr')}

=== 설계 원칙 ===
- {design_principles.get('behavior_enrichment', '행동 패턴 존중')}
- {design_principles.get('safety_first', '안전 최우선')}
- {design_principles.get('no_drilling', '타공 불필요')}
- {design_principles.get('customization', '맞춤 설계')}

=== 주요 제품 (예시) ===
{chr(10).join(products_list)}

=== 설치 정보 ===
- 출장 설치비: 기본 100,000원
- 지역별 추가: 서울 0원, 경기 20,000원, 인천 30,000원
- 배송비: 기본 6,000원, 제주 24,000원

=== 상담 원칙 ===
1. 고객과 고양이 정보를 자세히 파악
2. 고양이의 안전과 행복을 최우선으로 고려
3. 과도한 판매가 아닌 적절한 배치 권장
4. 동물행동학적 근거 제시

=== 필수 고려사항 ===
- 고양이 수, 나이, 체중, 품종, 성격
- 공간 크기 (가로, 세로, 천장 높이)
- 벽 재질 (콘크리트, 석고보드 등)
- 고양이 간 관계 (사이 좋음/안좋음)
- 건강 상태 및 문제 행동

=== 설계 가이드 ===
- 벽 발판 간격: 30-40cm (천천히 걸어 올라갈 수 있는 간격)
- 천장까지 최소: 건강한 성묘 7-10개, 노령묘 10-15개
- 다묘 가정: 2마리 이상 시 오르내리는 곳 2곳 이상
- 사이 안좋은 고양이: 시야가 닿지 않는 별도 영역
- 대형묘 (메인쿤 등): 넓은 발판 필요
- 먼치킨: 간격 최소화
- 노령묘: 완만한 경사, 안전 카펫 필수

=== 주요 FAQ ===
{chr(10).join(faq_list)}

=== 응답 스타일 ===
- 따뜻하고 친절한 톤
- 전문적이지만 이해하기 쉬운 설명
- 한국어로 자연스럽게 대화
- 이모지 적절히 사용 (🐱 🐾 등)
- 구체적인 수치와 근거 제시
- 고객의 상황에 공감

=== 상담 흐름 ===
1. 인사 및 상담 유형 확인
2. 필요 정보 수집 (공간, 고양이)
3. 전문가 분석 및 추천
4. 견적 안내
5. 추가 질문 응대
6. 카카오톡 상담 안내

중요: 항상 고양이의 행복과 안전을 최우선으로 생각하며, 과도한 제품 판매보다는 적절한 배치를 권장하세요.
타공 불필요한 안전한 설치 방식을 강조하세요.
"""

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        채팅 응답 생성 (컨텍스트 반영)

        Args:
            message: 사용자 메시지
            conversation_history: 대화 기록
            context: 추가 컨텍스트 (수집된 정보 등)

        Returns:
            AI 응답
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # 컨텍스트 정보 추가
        if context:
            context_info = f"\n\n현재 수집된 고객 정보:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            messages.append({
                "role": "system",
                "content": f"상담 중 수집된 정보를 참고하세요:{context_info}"
            })

        # 대화 기록 추가
        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            return response['message']['content']
        except Exception as e:
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다. 카카오톡으로 문의해주세요. (오류: {str(e)})"

    async def analyze_consultation_data(
        self,
        consultation_data: Dict
    ) -> Dict:
        """
        상담 데이터 분석 및 제품 추천

        Args:
            consultation_data: 수집된 상담 정보

        Returns:
            분석 결과 및 추천
        """
        # 실제 제품 데이터 로드
        products_info = json.dumps(self.products, ensure_ascii=False, indent=2)

        prompt = f"""
다음 고객의 상담 정보를 바탕으로 최적의 플레이캣 제품 배치를 추천해주세요.

=== 고객 정보 ===
{json.dumps(consultation_data, ensure_ascii=False, indent=2)}

=== 플레이캣 제품 정보 ===
{products_info}

=== 추천 요구사항 ===
1. 고양이 마릿수, 나이, 품종, 성격을 고려
2. 공간 크기에 맞춘 배치
3. 안전성을 최우선으로 고려
4. 예산 범위 내에서 최적 구성
5. 타공 불필요한 설치 방식 강조

다음 형식의 JSON으로 응답해주세요:
{{
    "analysis": {{
        "space_assessment": "공간 평가 (크기, 천장 높이, 적합성)",
        "cat_needs": ["고양이별 필요사항과 특성"],
        "safety_concerns": ["안전 고려사항"],
        "design_priorities": ["설계 우선순위"]
    }},
    "recommendations": {{
        "wall_walkers": {{
            "count": 숫자,
            "products": ["추천 제품 ID"],
            "spacing": "간격 설명",
            "reasoning": "선택 이유"
        }},
        "ceiling_walkers": {{
            "count": 숫자,
            "products": ["추천 제품 ID"],
            "reasoning": "선택 이유"
        }},
        "cat_towers": {{
            "count": 숫자,
            "products": ["추천 제품 ID"],
            "reasoning": "선택 이유"
        }},
        "accessories": {{
            "products": ["소모품 등"],
            "reasoning": "필요한 이유"
        }}
    }},
    "installation_tips": ["설치 시 주의사항"],
    "estimated_cost": {{
        "products": "제품 총액 (원)",
        "installation": "설치비 (원)",
        "shipping": "배송비 (원)",
        "total_min": "최소 예상 비용",
        "total_max": "최대 예상 비용"
    }},
    "special_notes": ["특별 권장사항 및 주의사항"],
    "next_steps": ["다음 단계 안내"]
}}
"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response['message']['content']

            # JSON 파싱
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                return json.loads(content.strip())
            except json.JSONDecodeError:
                return {
                    "analysis": {
                        "raw_response": content,
                        "note": "JSON 파싱 실패, 원문 응답"
                    },
                    "recommendations": {},
                    "special_notes": ["카카오톡 상담으로 정확한 견적을 받으세요"]
                }

        except Exception as e:
            return {
                "error": str(e),
                "message": "분석 중 오류가 발생했습니다. 카카오톡으로 문의해주세요.",
                "analysis": {},
                "recommendations": {}
            }

    async def get_product_info(self, product_query: str) -> str:
        """
        제품 정보 조회

        Args:
            product_query: 제품 관련 질문

        Returns:
            제품 정보 응답
        """
        products_str = json.dumps(self.products.get("products", []), ensure_ascii=False, indent=2)

        prompt = f"""
다음 제품 목록에서 고객의 질문에 맞는 제품을 찾아 친절하게 설명해주세요.

질문: {product_query}

제품 목록:
{products_str}

응답 형식:
- 제품명과 가격
- 주요 특징
- 사용 용도
- 적합한 고양이 유형
"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"제품 정보 조회 중 오류가 발생했습니다: {str(e)}"

    async def answer_faq(self, question: str) -> str:
        """
        FAQ 응답

        Args:
            question: 고객 질문

        Returns:
            FAQ 응답
        """
        faq_str = json.dumps(self.products.get("faq", []), ensure_ascii=False, indent=2)
        knowledge_str = json.dumps(self.knowledge.get("conversation_scenarios", {}), ensure_ascii=False, indent=2)

        prompt = f"""
고객의 질문에 대해 FAQ와 상담 지식을 바탕으로 친절하게 답변해주세요.

질문: {question}

FAQ:
{faq_str}

상담 지식:
{knowledge_str}

답변 시 주의사항:
- 구체적이고 명확하게
- 플레이캣의 특징 강조 (타공 불필요, 안전성 등)
- 필요시 추가 상담 (카카오톡) 안내
"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"


# 전역 인스턴스
ollama_client = PlaycatOllamaClient()
