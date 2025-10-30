from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import json


class ImageComposer:
    """이미지 합성 서비스"""

    def __init__(self, product_images_dir: str = "static/images/products"):
        self.product_images_dir = Path(product_images_dir)
        self.product_cache: Dict[str, Image.Image] = {}

    def load_product_image(self, product_id: str) -> Optional[Image.Image]:
        """
        제품 이미지 로드 (PNG, 투명 배경)

        Args:
            product_id: 제품 ID

        Returns:
            PIL Image 객체
        """
        if product_id in self.product_cache:
            return self.product_cache[product_id]

        image_path = self.product_images_dir / f"{product_id}.png"
        if not image_path.exists():
            return None

        img = Image.open(image_path).convert("RGBA")
        self.product_cache[product_id] = img
        return img

    def composite_simple(
        self,
        background_path: str,
        products: List[Dict],
        output_path: str
    ) -> str:
        """
        간단한 2D 이미지 합성 (PIL 사용)

        Args:
            background_path: 배경 이미지 (고객 실내 사진)
            products: 배치할 제품 리스트
                [
                    {
                        "id": "wall_walker_30",
                        "position": (x, y),
                        "scale": 1.0,
                        "rotation": 0
                    },
                    ...
                ]
            output_path: 출력 파일 경로

        Returns:
            합성된 이미지 경로
        """
        # 배경 이미지 로드
        background = Image.open(background_path).convert("RGBA")
        composite = background.copy()

        for product in products:
            product_img = self.load_product_image(product["id"])
            if not product_img:
                continue

            # 크기 조정
            scale = product.get("scale", 1.0)
            new_size = (
                int(product_img.width * scale),
                int(product_img.height * scale)
            )
            product_img = product_img.resize(new_size, Image.Resampling.LANCZOS)

            # 회전
            rotation = product.get("rotation", 0)
            if rotation != 0:
                product_img = product_img.rotate(rotation, expand=True)

            # 위치
            position = product.get("position", (0, 0))

            # 합성 (알파 채널 고려)
            composite.paste(product_img, position, product_img)

        # 저장
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        composite.convert("RGB").save(output, "JPEG", quality=95)

        return str(output)

    def composite_with_opencv(
        self,
        background_path: str,
        products: List[Dict],
        output_path: str
    ) -> str:
        """
        OpenCV를 사용한 이미지 합성 (더 정교한 블렌딩 가능)

        Args:
            background_path: 배경 이미지
            products: 제품 배치 정보
            output_path: 출력 경로

        Returns:
            합성된 이미지 경로
        """
        # 배경 이미지 로드
        background = cv2.imread(background_path)
        if background is None:
            raise ValueError(f"배경 이미지를 로드할 수 없습니다: {background_path}")

        background = cv2.cvtColor(background, cv2.COLOR_BGR2BGRA)

        for product in products:
            # 제품 이미지 로드
            product_img = self.load_product_image(product["id"])
            if not product_img:
                continue

            # PIL -> OpenCV
            product_cv = cv2.cvtColor(
                np.array(product_img),
                cv2.COLOR_RGBA2BGRA
            )

            # 크기 조정
            scale = product.get("scale", 1.0)
            new_size = (
                int(product_cv.shape[1] * scale),
                int(product_cv.shape[0] * scale)
            )
            product_cv = cv2.resize(product_cv, new_size)

            # 위치
            x, y = product.get("position", (0, 0))

            # 알파 블렌딩
            background = self._alpha_blend(background, product_cv, x, y)

        # 저장
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        result = cv2.cvtColor(background, cv2.COLOR_BGRA2BGR)
        cv2.imwrite(str(output), result, [cv2.IMWRITE_JPEG_QUALITY, 95])

        return str(output)

    def _alpha_blend(
        self,
        background: np.ndarray,
        foreground: np.ndarray,
        x: int,
        y: int
    ) -> np.ndarray:
        """
        알파 채널을 고려한 이미지 블렌딩

        Args:
            background: 배경 이미지 (BGRA)
            foreground: 전경 이미지 (BGRA)
            x, y: 배치 위치

        Returns:
            블렌딩된 이미지
        """
        bg_h, bg_w = background.shape[:2]
        fg_h, fg_w = foreground.shape[:2]

        # 경계 확인
        if x < 0 or y < 0 or x + fg_w > bg_w or y + fg_h > bg_h:
            # 범위를 벗어나면 클리핑
            x_start = max(0, x)
            y_start = max(0, y)
            x_end = min(bg_w, x + fg_w)
            y_end = min(bg_h, y + fg_h)

            fg_x_start = x_start - x
            fg_y_start = y_start - y
            fg_x_end = fg_x_start + (x_end - x_start)
            fg_y_end = fg_y_start + (y_end - y_start)

            foreground = foreground[fg_y_start:fg_y_end, fg_x_start:fg_x_end]
            x, y = x_start, y_start
            fg_h, fg_w = foreground.shape[:2]

        # 알파 채널 추출
        alpha = foreground[:, :, 3] / 255.0
        alpha = np.stack([alpha] * 3, axis=-1)

        # 블렌딩
        roi = background[y:y+fg_h, x:x+fg_w, :3]
        blended = (foreground[:, :, :3] * alpha + roi * (1 - alpha)).astype(np.uint8)

        # 결과 적용
        background[y:y+fg_h, x:x+fg_w, :3] = blended

        return background

    def auto_place_products(
        self,
        space_dimensions: Dict,
        products_config: List[Dict],
        cat_count: int
    ) -> List[Dict]:
        """
        자동 제품 배치 계산

        Args:
            space_dimensions: {"width": 300, "height": 250, "ceiling_height": 240}
            products_config: AI가 추천한 제품 구성
            cat_count: 고양이 수

        Returns:
            배치 정보가 추가된 제품 리스트
        """
        placed_products = []

        wall_walkers = []
        ceiling_walkers = []
        others = []

        # 제품 분류
        for product in products_config:
            if "wall_walker" in product["id"]:
                wall_walkers.append(product)
            elif "ceiling_walker" in product["id"]:
                ceiling_walkers.append(product)
            else:
                others.append(product)

        # 벽 발판 배치 (수직으로 계단식)
        wall_spacing = 35  # cm
        current_y = space_dimensions["ceiling_height"]

        for i, product in enumerate(wall_walkers):
            x_offset = 50 + (i % 2) * 60  # 지그재그 배치
            y_offset = current_y - (i * wall_spacing)

            placed_products.append({
                **product,
                "position": (x_offset, y_offset),
                "scale": 0.8,
                "rotation": 0
            })

        # 천장 발판 배치
        ceiling_y = 20
        ceiling_x_start = 100

        for i, product in enumerate(ceiling_walkers):
            placed_products.append({
                **product,
                "position": (ceiling_x_start + i * 100, ceiling_y),
                "scale": 0.8,
                "rotation": 0
            })

        # 기타 제품 배치
        for i, product in enumerate(others):
            placed_products.append({
                **product,
                "position": (150 + i * 80, 150),
                "scale": 0.7,
                "rotation": 0
            })

        return placed_products

    def add_annotations(
        self,
        image_path: str,
        annotations: List[Dict],
        output_path: str
    ) -> str:
        """
        이미지에 주석 추가 (제품명, 사이즈 표시 등)

        Args:
            image_path: 원본 이미지
            annotations: [{"position": (x, y), "text": "발판 30cm", "color": (255,0,0)}]
            output_path: 출력 경로

        Returns:
            주석이 추가된 이미지 경로
        """
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        # 폰트 (기본 폰트 사용, 필요시 TTF 폰트 경로 지정)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        for anno in annotations:
            position = anno.get("position", (0, 0))
            text = anno.get("text", "")
            color = anno.get("color", (255, 0, 0))

            # 텍스트 배경
            bbox = draw.textbbox(position, text, font=font)
            draw.rectangle(bbox, fill=(255, 255, 255, 200))

            # 텍스트
            draw.text(position, text, fill=color, font=font)

        # 저장
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        img.save(output, "JPEG", quality=95)

        return str(output)


# 전역 인스턴스
image_composer = ImageComposer()
