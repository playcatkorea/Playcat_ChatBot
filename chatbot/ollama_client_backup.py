import ollama
from typing import List, Dict, Optional
import json


class OllamaClient:
    """Ollama LLM 클라이언트"""

    def __init__(self, model: str = "qwen2.5:latest"):
        self.model = model
        self.system_prompt = """당신은 플레이캣(PLAYCAT)의 고양이 행동풍부화 전문 상담사입니다.

주요 역할:
1. 고객의 고양이와 설치 공간 정보를 수집
2. 고양이의 행동과 건강을 고려한 제품 배치 추천
3. 친절하고 전문적인 상담 제공

중요 원칙:
- 고양이의 관점에서 생각하고 답변
- 고양이의 안전과 행복을 최우선으로 고려
- 과도한 제품 판매가 아닌 적절한 배치 권장
- 고양이 행동풍부화의 중요성 강조

상담 시 고려사항:
- 고양이 수, 나이, 몸무게, 품종, 성격
- 공간 크기와 구조
- 고양이 간 관계 (사이 좋음/안좋음)
- 건강 상태 및 문제 행동
- 벽 발판 간격: 건강한 고양이 기준 30-40cm (천천히 걸어 올라갈 수 있는 간격)
- 천장까지 최소 6-7개 발판 필요
- 2마리 이상: 오르내리는 곳 2곳 이상 필요
- 관절 건강 고려 (특히 노령묘, 대형묘)

응답 스타일:
- 따뜻하고 공감하는 톤
- 전문적이지만 이해하기 쉬운 설명
- 한국어로 자연스럽게 대화
"""

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Ollama를 통해 채팅 응답 생성

        Args:
            message: 사용자 메시지
            conversation_history: 이전 대화 기록

        Returns:
            AI 응답 텍스트
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

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
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"

    async def analyze_consultation_data(
        self,
        consultation_data: Dict
    ) -> Dict:
        """
        상담 데이터를 분석하여 추천 제품 구성 생성

        Args:
            consultation_data: 상담 정보 딕셔너리

        Returns:
            분석 결과 및 추천 제품
        """
        prompt = f"""
다음 고객의 정보를 분석하여 최적의 캣워커 배치를 추천해주세요.

고객 정보:
{json.dumps(consultation_data, ensure_ascii=False, indent=2)}

다음 형식으로 JSON 응답을 작성해주세요:
{{
    "analysis": {{
        "space_assessment": "공간 평가",
        "cat_needs": ["고양이별 필요사항"],
        "safety_concerns": ["안전 고려사항"],
        "design_priorities": ["설계 우선순위"]
    }},
    "recommendations": {{
        "wall_walkers": {{
            "count": 숫자,
            "spacing": "간격 설명",
            "reasoning": "선택 이유"
        }},
        "ceiling_walkers": {{
            "count": 숫자,
            "reasoning": "선택 이유"
        }},
        "rest_spots": {{
            "count": 숫자,
            "placement": "배치 위치",
            "reasoning": "선택 이유"
        }},
        "scratchers": {{
            "count": 숫자,
            "type": "타입",
            "reasoning": "선택 이유"
        }},
        "houses": {{
            "count": 숫자,
            "reasoning": "선택 이유"
        }}
    }},
    "special_notes": ["특별 권장사항"],
    "estimated_budget": "예상 비용 범위"
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

            # JSON 파싱 시도
            try:
                # 코드 블록 제거
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                return json.loads(content.strip())
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 응답 반환
                return {
                    "analysis": {"raw_response": content},
                    "recommendations": {},
                    "special_notes": []
                }

        except Exception as e:
            return {
                "error": str(e),
                "analysis": {},
                "recommendations": {}
            }

    async def extract_information(
        self,
        user_message: str,
        field_name: str,
        field_description: str
    ) -> Optional[str]:
        """
        사용자 메시지에서 특정 정보 추출

        Args:
            user_message: 사용자 메시지
            field_name: 추출할 필드 이름
            field_description: 필드 설명

        Returns:
            추출된 정보
        """
        prompt = f"""
사용자 메시지에서 '{field_name}' 정보를 추출해주세요.
필드 설명: {field_description}

사용자 메시지:
{user_message}

추출된 정보만 간단히 답변해주세요. 정보가 없으면 "없음"이라고 답변하세요.
"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "정보 추출 전문가"},
                    {"role": "user", "content": prompt}
                ]
            )
            extracted = response['message']['content'].strip()
            return None if extracted == "없음" else extracted
        except Exception:
            return None


# 전역 인스턴스
ollama_client = OllamaClient()
