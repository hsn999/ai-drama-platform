from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw, ImageFont

from config import get_settings

settings = get_settings()
WORKFLOW_DIR = Path(__file__).parent / "workflows"


class ComfyUIClient:
    def __init__(self) -> None:
        self.base_url = settings.comfyui_base_url.rstrip("/")
        self.timeout = settings.comfyui_timeout

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/system_stats")
                return resp.status_code == 200
        except Exception:
            return False

    async def queue_prompt(self, workflow: dict) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow, "client_id": str(uuid.uuid4())},
            )
            resp.raise_for_status()
            return resp.json()["prompt_id"]

    async def wait_for_completion(self, prompt_id: str, poll_interval: float = 2.0) -> list[str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while True:
                resp = await client.get(f"{self.base_url}/history/{prompt_id}")
                resp.raise_for_status()
                history = resp.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    files: list[str] = []
                    for node_output in outputs.values():
                        for img in node_output.get("images", []):
                            files.append(img["filename"])
                    return files
                await asyncio.sleep(poll_interval)

    def load_workflow(self, name: str) -> dict:
        path = WORKFLOW_DIR / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    async def generate_image(
        self,
        prompt: str,
        output_dir: Path,
        prefix: str = "img",
        width: int = 768,
        height: int = 1024,
        checkpoint: str = "flux1-dev.safetensors",
        sampler_steps: int = 20,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        if await self.is_available() and self.load_workflow("character_portrait_flux.json"):
            try:
                workflow = self._build_simple_txt2img(prompt, width, height, checkpoint, sampler_steps)
                prompt_id = await self.queue_prompt(workflow)
                files = await self.wait_for_completion(prompt_id)
                if files:
                    src = Path("ComfyUI/output") / files[0]
                    if src.exists():
                        dst = output_dir / f"{prefix}_{uuid.uuid4().hex[:8]}.png"
                        dst.write_bytes(src.read_bytes())
                        return dst
            except Exception:
                pass
        return self._create_placeholder_image(output_dir, prefix, prompt, width, height)

    async def generate_video_from_prompt(
        self,
        prompt: str,
        output_dir: Path,
        prefix: str = "shot",
        duration: int = 5,
        fps: int = 24,
        width: int = 768,
        height: int = 1344,
        checkpoint: str = "flux1-dev.safetensors",
        sampler_steps: int = 20,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        if await self.is_available():
            try:
                keyframe = await self.generate_image(
                    prompt,
                    output_dir,
                    prefix=f"{prefix}_kf",
                    width=width,
                    height=height,
                    checkpoint=checkpoint,
                    sampler_steps=sampler_steps,
                )
                return await self._images_to_video([keyframe], output_dir, prefix, duration, fps)
            except Exception:
                pass
        return self._create_placeholder_video(output_dir, prefix, prompt, duration, fps)

    def _build_simple_txt2img(
        self,
        prompt: str,
        width: int,
        height: int,
        checkpoint: str = "flux1-dev.safetensors",
        sampler_steps: int = 20,
    ) -> dict:
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": uuid.uuid4().int % (2**32),
                    "steps": sampler_steps,
                    "cfg": 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality", "clip": ["4", 1]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "drama", "images": ["8", 0]}},
        }

    async def _images_to_video(
        self, images: list[Path], output_dir: Path, prefix: str, duration: int, fps: int
    ) -> Path:
        from video.ffmpeg import images_to_video

        out = output_dir / f"{prefix}_{uuid.uuid4().hex[:8]}.mp4"
        await images_to_video([str(p) for p in images], str(out), duration, fps)
        return out

    def _create_placeholder_image(
        self, output_dir: Path, prefix: str, prompt: str, width: int, height: int
    ) -> Path:
        img = Image.new("RGB", (width, height), color=(30, 30, 46))
        draw = ImageDraw.Draw(img)
        text = (prompt[:80] + "...") if len(prompt) > 80 else prompt
        draw.text((40, height // 2 - 20), f"[Placeholder]\n{text}", fill=(200, 200, 220))
        path = output_dir / f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        img.save(path)
        return path

    def _create_placeholder_video(
        self, output_dir: Path, prefix: str, prompt: str, duration: int, fps: int
    ) -> Path:
        frame = self._create_placeholder_image(output_dir, f"{prefix}_frame", prompt, 768, 1344)
        out = output_dir / f"{prefix}_{uuid.uuid4().hex[:8]}.mp4"
        from video.ffmpeg import images_to_video

        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            # sync fallback
            import subprocess

            cmd = [
                settings.ffmpeg_path,
                "-y",
                "-loop",
                "1",
                "-i",
                str(frame),
                "-c:v",
                "libx264",
                "-t",
                str(duration),
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                str(out),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        else:
            loop.run_until_complete(images_to_video([str(frame)], str(out), duration, fps))
        return out


comfyui_client = ComfyUIClient()
