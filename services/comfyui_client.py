import aiohttp
import asyncio
import json
import uuid
import os
from typing import Dict, List, Optional
from pathlib import Path
import websocket
import urllib.request
import urllib.parse


class ComfyUIClient:
    """ComfyUI API 클라이언트 - Playcat 챗봇용"""

    def __init__(
        self,
        server_address: str = "127.0.0.1:8188",
        client_id: str = None,
        comfyui_path: str = r"C:\StabilityMatrix-win-x64\Data\Packages\ComfyUI"
    ):
        self.server_address = server_address
        self.client_id = client_id or str(uuid.uuid4())
        self.comfyui_path = Path(comfyui_path)
        self.workflows_dir = self.comfyui_path / "user" / "default" / "workflows"
        self.output_dir = self.comfyui_path / "output"

    def _get_url(self, endpoint: str) -> str:
        """API URL 생성"""
        return f"http://{self.server_address}/{endpoint}"

    async def upload_image(self, image_path: str) -> str:
        """
        이미지를 ComfyUI에 업로드

        Args:
            image_path: 업로드할 이미지 경로

        Returns:
            업로드된 이미지 이름
        """
        url = self._get_url("upload/image")

        with open(image_path, "rb") as f:
            files = {"image": f}
            data = {"overwrite": "true"}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, files=files) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("name")
                    else:
                        raise Exception(f"Image upload failed: {response.status}")

    async def queue_prompt(self, prompt: Dict) -> str:
        """
        워크플로우를 실행 큐에 추가

        Args:
            prompt: 워크플로우 프롬프트 (JSON)

        Returns:
            프롬프트 ID
        """
        url = self._get_url("prompt")

        data = {
            "prompt": prompt,
            "client_id": self.client_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("prompt_id")
                else:
                    raise Exception(f"Prompt queue failed: {response.status}")

    async def get_history(self, prompt_id: str) -> Dict:
        """프롬프트 실행 히스토리 조회"""
        url = self._get_url(f"history/{prompt_id}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}

    async def wait_for_completion(
        self,
        prompt_id: str,
        timeout: int = 600
    ) -> Dict:
        """
        워크플로우 완료 대기

        Args:
            prompt_id: 프롬프트 ID
            timeout: 최대 대기 시간 (초)

        Returns:
            실행 결과
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Workflow timed out after {timeout}s")

            history = await self.get_history(prompt_id)

            if prompt_id in history:
                return history[prompt_id]

            await asyncio.sleep(2)

    async def download_output(
        self,
        filename: str,
        subfolder: str = "",
        folder_type: str = "output"
    ) -> bytes:
        """출력 파일 다운로드"""
        url_values = urllib.parse.urlencode({
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        })

        url = self._get_url(f"view?{url_values}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Download failed: {response.status}")

    def _load_workflow(self, workflow_name: str) -> Dict:
        """워크플로우 JSON 로드"""
        workflow_path = self.workflows_dir / f"{workflow_name}.json"

        with open(workflow_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def correct_photo(
        self,
        room_image_path: str,
        output_path: str = None
    ) -> str:
        """
        사진 보정 (정면 변환, 품질 개선)

        Args:
            room_image_path: 원본 방 사진 경로
            output_path: 결과 저장 경로

        Returns:
            보정된 이미지 경로
        """
        # PLAYCAT_PHOTO_CORRECTION 워크플로우 로드
        workflow = self._load_workflow("PLAYCAT_PHOTO_CORRECTION")

        # 이미지 업로드
        uploaded_image = await self.upload_image(room_image_path)

        # 워크플로우에서 이미지 파일명 설정
        for node_id, node in workflow["nodes"].items():
            if node.get("class_type") == "LoadImage":
                node["inputs"]["image"] = uploaded_image

        # 실행
        prompt_id = await self.queue_prompt({"prompt": workflow})

        # 완료 대기
        result = await self.wait_for_completion(prompt_id)

        # 결과 다운로드
        for node_output in result.get("outputs", {}).values():
            if "images" in node_output:
                first_image = node_output["images"][0]
                image_data = await self.download_output(
                    first_image["filename"],
                    first_image.get("subfolder", ""),
                    first_image.get("type", "output")
                )

                # 저장
                if not output_path:
                    output_dir = Path("static/corrected")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"corrected_{uuid.uuid4()}.png"

                with open(output_path, "wb") as f:
                    f.write(image_data)

                return str(output_path)

        raise Exception("No output generated")

    async def product_composition(
        self,
        room_image_path: str,
        products: List[Dict],
        lora_name: str = "playcat_products.safetensors",
        output_path: str = None
    ) -> str:
        """
        제품 합성 실행

        Args:
            room_image_path: 실내 사진 경로
            products: 제품 리스트 [{"type": "wall_walker", "material": "wood", ...}]
            lora_name: 사용할 LoRA 모델
            output_path: 결과 저장 경로

        Returns:
            합성된 이미지 경로
        """
        # 워크플로우 로드
        workflow = self._load_workflow("product_composition")

        # 이미지 업로드
        uploaded_image = await self.upload_image(room_image_path)

        # 프롬프트 생성
        product_descriptions = []
        for product in products:
            product_type = product.get("type", "wall walker")
            material = product.get("material", "wooden")
            product_descriptions.append(f"{material} {product_type}")

        prompt_text = workflow["prompt_template"]["positive"].format(
            product_type=", ".join(product_descriptions),
            material=products[0].get("material", "wooden"),
            wall_type="white wall"
        )

        # 워크플로우 커스터마이징
        prompt = workflow["nodes"].copy()
        prompt["3"]["inputs"]["image"] = uploaded_image
        prompt["8"]["inputs"]["text"] = prompt_text

        # 실행
        prompt_id = await self.queue_prompt(prompt)

        # 완료 대기
        result = await self.wait_for_completion(prompt_id)

        # 결과 다운로드
        output_node = result["outputs"]["12"]
        output_images = output_node["images"]

        if output_images:
            first_output = output_images[0]
            image_data = await self.download_output(
                first_output["filename"],
                first_output.get("subfolder", ""),
                first_output.get("type", "output")
            )

            # 저장
            if not output_path:
                output_dir = Path("static/composites")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"composition_{uuid.uuid4()}.png"

            with open(output_path, "wb") as f:
                f.write(image_data)

            return str(output_path)

        raise Exception("No output generated")

    async def cat_animation(
        self,
        base_image_path: str,
        cat_image_path: str,
        activity_prompt: str,
        output_path: str = None
    ) -> str:
        """
        고양이 동영상 생성

        Args:
            base_image_path: 제품 합성 이미지
            cat_image_path: 고양이 사진
            activity_prompt: 활동 프롬프트
            output_path: 결과 저장 경로

        Returns:
            생성된 동영상 경로
        """
        # 워크플로우 로드
        workflow = self._load_workflow("cat_animation")

        # 이미지 업로드
        uploaded_base = await self.upload_image(base_image_path)
        uploaded_cat = await self.upload_image(cat_image_path)

        # 프롬프트 커스터마이징
        prompt = workflow["nodes"].copy()
        prompt["2"]["inputs"]["image"] = uploaded_base
        prompt["3"]["inputs"]["image"] = uploaded_cat
        prompt["9"]["inputs"]["text"] = activity_prompt

        # 실행
        prompt_id = await self.queue_prompt(prompt)

        # 완료 대기 (동영상은 시간이 더 걸림)
        result = await self.wait_for_completion(prompt_id, timeout=900)

        # 결과 다운로드
        output_node = result["outputs"]["14"]
        output_videos = output_node.get("gifs", [])

        if output_videos:
            first_output = output_videos[0]
            video_data = await self.download_output(
                first_output["filename"],
                first_output.get("subfolder", ""),
                first_output.get("type", "output")
            )

            # 저장
            if not output_path:
                output_dir = Path("static/animations")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"animation_{uuid.uuid4()}.mp4"

            with open(output_path, "wb") as f:
                f.write(video_data)

            return str(output_path)

        raise Exception("No video generated")

    async def generate_cat_video_with_audio(
        self,
        text_prompt: str,
        video_positive_prompt: str,
        video_negative_prompt: str,
        audio_prompt: str,
        audio_negative_prompt: str = "",
        video_duration: float = 3.375,
        output_path: str = None
    ) -> Dict[str, str]:
        """
        FLUX + WAN I2V + MMAudio 통합 워크플로
        텍스트 → 이미지 → 비디오 → 오디오 생성

        Args:
            text_prompt: FLUX 이미지 생성 프롬프트
            video_positive_prompt: WAN I2V 긍정 프롬프트
            video_negative_prompt: WAN I2V 부정 프롬프트
            audio_prompt: MMAudio 프롬프트
            audio_negative_prompt: MMAudio 부정 프롬프트
            video_duration: 비디오 길이 (초) - 기본 3.375초 (81프레임)
            output_path: 결과 저장 경로

        Returns:
            {
                "image": "생성된 이미지 경로",
                "video": "오디오 포함 비디오 경로",
                "prompt_id": "프롬프트 ID"
            }
        """
        # 워크플로 로드
        workflow = self._load_workflow("FLUX_KREA_WAN_MMAudio_Complete")

        # 노드 ID 찾기 (워크플로 구조에 맞게)
        nodes = workflow.get("nodes", [])

        # FLUX 텍스트 프롬프트 설정 (node 45 - CLIPTextEncode)
        for node in nodes:
            if node.get("id") == 45 and node.get("type") == "CLIPTextEncode":
                node["widgets_values"] = [text_prompt]

        # WAN I2V Positive 프롬프트 설정 (node 1005)
        for node in nodes:
            if node.get("id") == 1005 and node.get("type") == "CLIPTextEncode":
                node["widgets_values"] = [video_positive_prompt]

        # WAN I2V Negative 프롬프트 설정 (node 1004)
        for node in nodes:
            if node.get("id") == 1004 and node.get("type") == "CLIPTextEncode":
                node["widgets_values"] = [video_negative_prompt]

        # WAN I2V 비디오 길이 설정 (node 1009 - WanImageToVideo)
        # duration(초)을 프레임으로 변환: 프레임 = (duration * 24) + 1
        video_frames = int(video_duration * 24) + 1
        for node in nodes:
            if node.get("id") == 1009 and node.get("type") == "WanImageToVideo":
                # widgets_values: [width, height, length, batch_size]
                node["widgets_values"][2] = video_frames

        # MMAudio 프롬프트 설정 (node 3013 - MMAudioSampler)
        for node in nodes:
            if node.get("id") == 3013 and node.get("type") == "MMAudioSampler":
                # widgets_values: [duration, steps, cfg, seed, prompt, negative_prompt, ...]
                node["widgets_values"][2] = video_duration  # duration
                node["widgets_values"][5] = audio_prompt  # prompt
                node["widgets_values"][6] = audio_negative_prompt  # negative_prompt

        # 실행
        prompt_id = await self.queue_prompt(workflow)
        print(f"🎬 비디오 생성 시작: {prompt_id}")
        print(f"  📝 프롬프트: {text_prompt[:50]}...")
        print(f"  ⏱️  비디오 길이: {video_duration}초 ({video_frames}프레임)")

        # 완료 대기 (비디오+오디오 생성은 시간이 오래 걸림)
        result = await self.wait_for_completion(prompt_id, timeout=1200)
        print(f"✅ 비디오 생성 완료: {prompt_id}")

        # 결과 수집
        outputs = result.get("outputs", {})
        result_paths = {
            "image": None,
            "video": None,
            "prompt_id": prompt_id
        }

        # 이미지 찾기 (node 9 - SaveImage)
        if "9" in outputs and "images" in outputs["9"]:
            first_image = outputs["9"]["images"][0]
            image_data = await self.download_output(
                first_image["filename"],
                first_image.get("subfolder", ""),
                first_image.get("type", "output")
            )

            # 저장
            output_dir = Path("static/generated")
            output_dir.mkdir(parents=True, exist_ok=True)
            image_path = output_dir / f"flux_image_{prompt_id}.png"

            with open(image_path, "wb") as f:
                f.write(image_data)

            result_paths["image"] = str(image_path)
            print(f"  🖼️  이미지: {image_path}")

        # 비디오 찾기 (node 3015 - VHS_VideoCombine)
        if "3015" in outputs:
            # VHS_VideoCombine는 'gifs' 키를 사용할 수 있음
            video_output = None
            if "gifs" in outputs["3015"]:
                video_output = outputs["3015"]["gifs"][0]
            elif "videos" in outputs["3015"]:
                video_output = outputs["3015"]["videos"][0]

            if video_output:
                video_data = await self.download_output(
                    video_output["filename"],
                    video_output.get("subfolder", ""),
                    video_output.get("type", "output")
                )

                # 저장
                output_dir = Path("static/generated")
                output_dir.mkdir(parents=True, exist_ok=True)

                if output_path:
                    video_path = Path(output_path)
                else:
                    video_path = output_dir / f"cat_video_{prompt_id}.mp4"

                with open(video_path, "wb") as f:
                    f.write(video_data)

                result_paths["video"] = str(video_path)
                print(f"  🎥 비디오: {video_path}")

        return result_paths

    async def batch_generate(
        self,
        room_image: str,
        cat_image: str,
        products: List[Dict],
        activity_prompt: str
    ) -> Dict[str, str]:
        """
        전체 파이프라인 실행

        Args:
            room_image: 실내 사진
            cat_image: 고양이 사진
            products: 제품 리스트
            activity_prompt: 활동 프롬프트

        Returns:
            {
                "composition": "합성 이미지 경로",
                "animation": "동영상 경로"
            }
        """
        # 1. 제품 합성
        composition_path = await self.product_composition(
            room_image_path=room_image,
            products=products
        )

        # 2. 고양이 동영상 생성
        animation_path = await self.cat_animation(
            base_image_path=composition_path,
            cat_image_path=cat_image,
            activity_prompt=activity_prompt
        )

        return {
            "composition": composition_path,
            "animation": animation_path
        }


# 전역 인스턴스
comfyui_client = ComfyUIClient()
