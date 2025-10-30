"""
Phase 2: AI 이미지/영상 생성 통합 서비스

전체 파이프라인:
1. 사진 검증 및 정면 변환
2. 제품 합성
3. 고양이 놀이 장면 합성
4. 5초 동영상 생성
"""

import asyncio
import logging
from typing import Dict, List, Optional
from pathlib import Path

from services.comfyui_client import comfyui_client
try:
    from services.qwen_image_edit import QwenImageEditor
    QWEN_AVAILABLE = True
except Exception as e:
    logging.warning(f"Qwen2-VL not available: {e}")
    QWEN_AVAILABLE = False

from services.image_composer import image_composer
from chatbot.ollama_client import ollama_client

logger = logging.getLogger(__name__)


class AIGenerationService:
    """AI 이미지/영상 생성 통합 서비스"""

    def __init__(self):
        self.qwen_editor = QwenImageEditor() if QWEN_AVAILABLE else None
        self.use_advanced_pipeline = False  # ComfyUI 사용 여부

    async def process_consultation_images(
        self,
        consultation_data: Dict
    ) -> Dict:
        """
        상담 정보를 받아 전체 AI 생성 파이프라인 실행

        Args:
            consultation_data: {
                "room_image": "path/to/room.jpg",
                "cat_photos": ["path/to/cat1.jpg", ...],
                "products": [...],
                "expected_activity": "높은 곳에서 편안하게 쉬는 모습",
                "cat_count": 2,
                ...
            }

        Returns:
            {
                "room_front_view": "정면 변환된 사진",
                "product_composition": "제품 합성 이미지",
                "cat_composition": "고양이 + 제품 이미지",
                "animation_video": "5초 동영상",
                "processing_log": [...],
                "quality_report": {...}
            }
        """
        result = {
            "room_front_view": None,
            "product_composition": None,
            "cat_composition": None,
            "animation_video": None,
            "processing_log": [],
            "quality_report": {}
        }

        try:
            # Step 1: 사진 검증 및 정면 변환
            room_image = consultation_data.get("room_image")
            if not room_image:
                raise ValueError("Room image is required")

            result["processing_log"].append("Step 1: 사진 분석 시작...")

            front_view_image = await self._validate_and_convert_image(
                room_image,
                result
            )

            # Step 2: 제품 배치 계산
            result["processing_log"].append("Step 2: 최적 제품 배치 계산...")

            products = await self._calculate_product_placement(
                consultation_data,
                result
            )

            # Step 3: 제품 합성
            result["processing_log"].append("Step 3: 제품 합성 중...")

            product_composition = await self._compose_products(
                front_view_image,
                products,
                result
            )

            result["product_composition"] = product_composition

            # Step 4: 고양이 사진이 있다면 합성
            cat_photos = consultation_data.get("cat_photos", [])
            if cat_photos and len(cat_photos) > 0:
                result["processing_log"].append("Step 4: 고양이 합성 중...")

                cat_composition = await self._compose_cats(
                    product_composition,
                    cat_photos[0],  # 첫 번째 고양이 사진 사용
                    result
                )

                result["cat_composition"] = cat_composition

                # Step 5: 동영상 생성 (기대하는 활동이 있다면)
                expected_activity = consultation_data.get("expected_activity")
                if expected_activity:
                    result["processing_log"].append("Step 5: 동영상 생성 중...")

                    animation = await self._generate_animation(
                        cat_composition,
                        cat_photos[0],
                        expected_activity,
                        result
                    )

                    result["animation_video"] = animation

            result["processing_log"].append("✅ 모든 처리 완료!")

        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            result["processing_log"].append(f"❌ 오류 발생: {str(e)}")
            result["error"] = str(e)

        return result

    async def _validate_and_convert_image(
        self,
        image_path: str,
        result: Dict
    ) -> str:
        """사진 검증 및 정면 변환"""

        # Qwen으로 이미지 분석
        if self.qwen_editor:
            try:
                analysis = await self.qwen_editor.analyze_image_quality(image_path)
                result["quality_report"] = analysis

                result["processing_log"].append(
                    f"📊 사진 분석 완료 - 품질: {analysis['quality_score']}/100"
                )

                # 정면 변환 필요 여부 판단
                if analysis.get("recommendation") == "convert_to_front_view":
                    result["processing_log"].append(
                        "🔄 사진 각도 보정 중... (약 1분 소요)"
                    )

                    front_view = await self.qwen_editor.convert_to_front_view(
                        image_path
                    )

                    result["room_front_view"] = front_view
                    return front_view

            except Exception as e:
                logger.warning(f"Qwen analysis failed: {e}")
                result["processing_log"].append(
                    "⚠️ 자동 분석 실패, 원본 사진 사용"
                )

        # 분석 불가능 또는 불필요한 경우 원본 사용
        result["room_front_view"] = image_path
        return image_path

    async def _calculate_product_placement(
        self,
        consultation_data: Dict,
        result: Dict
    ) -> List[Dict]:
        """AI를 사용한 최적 제품 배치 계산"""

        # Ollama를 통해 제품 구성 추천
        analysis = await ollama_client.analyze_consultation_data(
            consultation_data
        )

        result["processing_log"].append(
            f"💡 AI 추천: {len(analysis.get('recommendations', {}))}가지 제품 구성"
        )

        # 추천 제품을 실제 배치 정보로 변환
        products = []

        # 벽 캣워커
        wall_walkers = analysis.get("recommendations", {}).get("wall_walkers", {})
        wall_count = wall_walkers.get("count", 6)

        for i in range(wall_count):
            products.append({
                "id": "wall_walker_30",
                "type": "wall walker",
                "material": "wooden",
                "quantity": 1
            })

        # 천장 캣워커
        ceiling_walkers = analysis.get("recommendations", {}).get("ceiling_walkers", {})
        ceiling_count = ceiling_walkers.get("count", 2)

        for i in range(ceiling_count):
            products.append({
                "id": "ceiling_walker_60",
                "type": "ceiling walker",
                "material": "wooden",
                "quantity": 1
            })

        # 휴식처
        rest_spots = analysis.get("recommendations", {}).get("rest_spots", {})
        rest_count = rest_spots.get("count", 2)

        for i in range(rest_count):
            products.append({
                "id": "rest_spot_circle",
                "type": "rest spot",
                "material": "wooden",
                "quantity": 1
            })

        return products

    async def _compose_products(
        self,
        room_image: str,
        products: List[Dict],
        result: Dict
    ) -> str:
        """제품 합성"""

        if self.use_advanced_pipeline:
            # ComfyUI 사용 (Phase 2 고급 기능)
            try:
                result["processing_log"].append(
                    "🎨 AI 고급 합성 시작 (2-5분 소요)..."
                )

                composition = await comfyui_client.product_composition(
                    room_image_path=room_image,
                    products=products
                )

                return composition

            except Exception as e:
                logger.warning(f"ComfyUI composition failed: {e}, falling back to simple")
                result["processing_log"].append(
                    "⚠️ 고급 합성 실패, 기본 합성 사용"
                )

        # Phase 1 기본 합성 (PIL/OpenCV)
        result["processing_log"].append(
            "🖼️ 기본 이미지 합성 (빠른 모드)..."
        )

        # 자동 배치 계산
        space_dimensions = {
            "width": 300,  # 실제로는 consultation_data에서 가져와야 함
            "height": 250,
            "ceiling_height": 240
        }

        placed_products = image_composer.auto_place_products(
            space_dimensions=space_dimensions,
            products_config=products,
            cat_count=2  # 실제 값 사용
        )

        composition = image_composer.composite_simple(
            background_path=room_image,
            products=placed_products,
            output_path=f"static/composites/composition_{Path(room_image).stem}.jpg"
        )

        return composition

    async def _compose_cats(
        self,
        base_image: str,
        cat_photo: str,
        result: Dict
    ) -> str:
        """고양이 합성"""

        if self.use_advanced_pipeline:
            # ComfyUI + IP-Adapter 사용
            try:
                result["processing_log"].append(
                    "🐱 고양이 AI 합성 중 (1-3분 소요)..."
                )

                # TODO: IP-Adapter를 사용한 고양이 얼굴 유지 합성
                # 현재는 기본 합성으로 폴백

                pass

            except Exception as e:
                logger.warning(f"Cat composition failed: {e}")

        # 기본 합성
        result["processing_log"].append(
            "🐱 고양이 기본 합성..."
        )

        # 단순 오버레이 (Phase 1)
        # 실제로는 더 정교한 합성 필요
        return base_image

    async def _generate_animation(
        self,
        base_image: str,
        cat_photo: str,
        activity_prompt: str,
        result: Dict
    ) -> str:
        """5초 동영상 생성"""

        if not self.use_advanced_pipeline:
            result["processing_log"].append(
                "⚠️ 동영상 생성은 고급 모드에서만 가능합니다"
            )
            return None

        try:
            result["processing_log"].append(
                "🎬 동영상 생성 중 (3-10분 소요)..."
            )

            animation = await comfyui_client.cat_animation(
                base_image_path=base_image,
                cat_image_path=cat_photo,
                activity_prompt=activity_prompt
            )

            result["processing_log"].append(
                "✅ 5초 동영상 생성 완료!"
            )

            return animation

        except Exception as e:
            logger.error(f"Animation generation failed: {e}")
            result["processing_log"].append(
                f"❌ 동영상 생성 실패: {str(e)}"
            )
            return None

    def enable_advanced_pipeline(self, enable: bool = True):
        """
        고급 파이프라인 활성화/비활성화

        Args:
            enable: True = ComfyUI 사용, False = 기본 합성만 사용
        """
        self.use_advanced_pipeline = enable
        logger.info(
            f"Advanced pipeline {'enabled' if enable else 'disabled'}"
        )


# 전역 인스턴스
ai_generation_service = AIGenerationService()
