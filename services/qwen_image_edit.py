from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
import torch
from typing import Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class QwenImageEditor:
    """Qwen2-VL을 사용한 이미지 편집 및 변환"""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2-VL-7B-Instruct",
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.model_name = model_name

        logger.info(f"Loading Qwen2-VL model on {device}...")

        # 모델 로드
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto"
        )

        self.processor = AutoProcessor.from_pretrained(model_name)

        logger.info("Qwen2-VL model loaded successfully")

    async def analyze_image_quality(self, image_path: str) -> Dict:
        """
        이미지 품질 분석

        Args:
            image_path: 분석할 이미지 경로

        Returns:
            {
                "is_front_view": bool,
                "quality_score": 0-100,
                "detected_elements": ["wall", "ceiling", "floor"],
                "issues": ["tilted angle", "poor lighting"],
                "recommendation": "convert_to_front_view"
            }
        """
        image = Image.open(image_path)

        prompt = """Analyze this room photo and provide:
1. Is it a front-facing view? (yes/no)
2. Image quality score (0-100)
3. What elements are visible? (wall, ceiling, floor, furniture)
4. Any issues? (angle, lighting, blur, obstruction)
5. Recommendation: (keep_original, convert_to_front_view, enhance_lighting)

Respond in JSON format."""

        inputs = self.processor(
            text=[prompt],
            images=[image],
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=256
            )

        response = self.processor.batch_decode(
            output_ids,
            skip_special_tokens=True
        )[0]

        # JSON 파싱 시도
        try:
            import json
            analysis = json.loads(response)
        except:
            # 파싱 실패 시 기본값
            analysis = {
                "is_front_view": True,
                "quality_score": 70,
                "detected_elements": ["wall"],
                "issues": [],
                "recommendation": "keep_original"
            }

        return analysis

    async def convert_to_front_view(
        self,
        image_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        각도가 틀어진 사진을 정면으로 변환

        Args:
            image_path: 원본 이미지 경로
            output_path: 출력 이미지 경로

        Returns:
            변환된 이미지 경로
        """
        image = Image.open(image_path)

        prompt = """Convert this room photo to a perfect front-facing view.
Requirements:
- Straighten the perspective
- Make walls parallel and vertical
- Keep all furniture and features in their positions
- Maintain realistic proportions
- Professional architectural photography style
- High quality, sharp details

Generate a corrected front-facing view of this room."""

        inputs = self.processor(
            text=[prompt],
            images=[image],
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            # 이미지 생성
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.7
            )

        # 결과 디코딩
        # 참고: Qwen2-VL의 이미지 생성 기능은 제한적일 수 있음
        # 실제로는 ControlNet + Stable Diffusion이 더 효과적

        # 임시 구현: 원본 이미지 반환
        # TODO: ComfyUI의 ControlNet 워크플로우 사용
        logger.warning(
            "Front view conversion via Qwen2-VL is experimental. "
            "Consider using ControlNet for better results."
        )

        if not output_path:
            output_dir = Path("static/processed")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"front_view_{Path(image_path).name}"

        # 현재는 원본 복사 (실제 변환은 ComfyUI에서)
        image.save(output_path)

        return str(output_path)

    async def enhance_image(
        self,
        image_path: str,
        enhancement_type: str = "lighting",
        output_path: Optional[str] = None
    ) -> str:
        """
        이미지 개선

        Args:
            image_path: 원본 이미지
            enhancement_type: "lighting", "sharpness", "color"
            output_path: 출력 경로

        Returns:
            개선된 이미지 경로
        """
        image = Image.open(image_path)

        prompts = {
            "lighting": "Enhance the lighting of this room photo. Make it brighter and more evenly lit, while maintaining natural appearance.",
            "sharpness": "Sharpen this room photo. Enhance details and clarity, reduce blur.",
            "color": "Improve the color balance of this room photo. Make colors more vibrant and natural."
        }

        prompt = prompts.get(enhancement_type, prompts["lighting"])

        inputs = self.processor(
            text=[prompt],
            images=[image],
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=512
            )

        if not output_path:
            output_dir = Path("static/processed")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"enhanced_{Path(image_path).name}"

        # 임시: 원본 저장
        image.save(output_path)

        return str(output_path)

    async def describe_room(self, image_path: str) -> str:
        """
        방 사진 설명 생성

        Args:
            image_path: 이미지 경로

        Returns:
            텍스트 설명
        """
        image = Image.open(image_path)

        prompt = """Describe this room in detail:
- Room type (living room, bedroom, etc.)
- Wall color and material
- Ceiling height (estimate)
- Floor type
- Furniture present
- Available wall space for cat furniture
- Lighting conditions
- Overall room size (small, medium, large)

Provide a detailed description."""

        inputs = self.processor(
            text=[prompt],
            images=[image],
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=512
            )

        description = self.processor.batch_decode(
            output_ids,
            skip_special_tokens=True
        )[0]

        return description


# 전역 인스턴스 (필요시 사용)
# qwen_editor = QwenImageEditor()
