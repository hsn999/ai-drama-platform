from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw, ImageFont

from config import ROOT_DIR, get_settings

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

    async def wait_for_completion(self, prompt_id: str, poll_interval: float = 2.0) -> list[dict[str, str]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while True:
                resp = await client.get(f"{self.base_url}/history/{prompt_id}")
                resp.raise_for_status()
                history = resp.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    files: list[dict[str, str]] = []
                    for node_output in outputs.values():
                        for img in node_output.get("images", []):
                            files.append(
                                {
                                    "filename": img["filename"],
                                    "subfolder": img.get("subfolder", ""),
                                    "type": img.get("type", "output"),
                                }
                            )
                    return files
                await asyncio.sleep(poll_interval)

    async def download_image(self, filename: str, subfolder: str = "", type_: str = "output") -> bytes:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/view",
                params={"filename": filename, "subfolder": subfolder, "type": type_},
            )
            resp.raise_for_status()
            return resp.content

    def _resolve_output_file(self, filename: str) -> Path | None:
        candidates: list[Path] = []
        if settings.comfyui_output_dir:
            candidates.append(settings.comfyui_output_dir / filename)
        candidates.extend(
            [
                Path("/hy-tmp/ComfyUI/output") / filename,
                Path("ComfyUI/output") / filename,
                ROOT_DIR.parent / "ComfyUI" / "output" / filename,
            ]
        )
        for path in candidates:
            if path.is_file():
                return path
        return None

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
        if await self.is_available():
            try:
                if "flux" in checkpoint.lower():
                    workflow = self._build_flux_txt2img(prompt, width, height, sampler_steps)
                else:
                    workflow = self._build_simple_txt2img(
                        prompt, width, height, checkpoint, sampler_steps
                    )
                prompt_id = await self.queue_prompt(workflow)
                images = await self.wait_for_completion(prompt_id)
                if images:
                    img = images[0]
                    dst = output_dir / f"{prefix}_{uuid.uuid4().hex[:8]}.png"
                    try:
                        dst.write_bytes(
                            await self.download_image(
                                img["filename"], img.get("subfolder", ""), img.get("type", "output")
                            )
                        )
                        return dst
                    except Exception:
                        src = self._resolve_output_file(img["filename"])
                        if src:
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
        motion: str = "zoom_in",
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
                return await self._image_to_kenburns_clip(
                    keyframe, output_dir, prefix, duration, fps, motion, width, height
                )
            except Exception:
                pass
        return await self._create_placeholder_video(
            output_dir, prefix, prompt, duration, fps, motion, width, height
        )

    def _flux_negative(self, prompt: str) -> str:
        base = "blurry, low quality, text, watermark"
        pl = prompt.lower()
        if any(k in pl for k in ("dog", "puppy", "cat", "animal only", "no human", "no people")):
            base += ", human, person, man, woman, boy, girl, portrait, face"
        return base

    def _build_flux_txt2img(
        self,
        prompt: str,
        width: int,
        height: int,
        sampler_steps: int = 20,
    ) -> dict:
        """Flux 分拆加载：UNet + DualCLIP + VAE（适配魔搭 FP8 等非合并权重）."""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": uuid.uuid4().int % (2**32),
                    "steps": sampler_steps,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": settings.flux_unet,
                    "weight_dtype": "default",
                },
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1},
            },
            "10": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": settings.flux_clip_l,
                    "clip_name2": settings.flux_clip_t5,
                    "type": "flux",
                },
            },
            "11": {
                "class_type": "VAELoader",
                "inputs": {"vae_name": settings.flux_vae},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["10", 0]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": self._flux_negative(prompt), "clip": ["10", 0]},
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["11", 0]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "drama", "images": ["8", 0]},
            },
        }

    def _build_simple_txt2img(
        self,
        prompt: str,
        width: int,
        height: int,
        checkpoint: str = "flux1-dev.safetensors",
        sampler_steps: int = 20,
    ) -> dict:
        is_flux = "flux" in checkpoint.lower()
        cfg = 3.5 if is_flux else 7.5
        sampler = "euler" if is_flux else "euler"
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": uuid.uuid4().int % (2**32),
                    "steps": sampler_steps,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": "simple" if is_flux else "normal",
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

    async def _image_to_kenburns_clip(
        self,
        image: Path,
        output_dir: Path,
        prefix: str,
        duration: int,
        fps: int,
        motion: str,
        width: int,
        height: int,
    ) -> Path:
        from video.ffmpeg import image_to_kenburns_clip

        out = output_dir / f"{prefix}_{uuid.uuid4().hex[:8]}.mp4"
        await image_to_kenburns_clip(
            str(image),
            str(out),
            float(duration),
            resolution=f"{width}x{height}",
            fps=fps,
            motion=motion,
        )
        return out

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

    async def _create_placeholder_video(
        self,
        output_dir: Path,
        prefix: str,
        prompt: str,
        duration: int,
        fps: int,
        motion: str = "zoom_in",
        width: int = 768,
        height: int = 1344,
    ) -> Path:
        frame = self._create_placeholder_image(output_dir, f"{prefix}_frame", prompt, width, height)
        return await self._image_to_kenburns_clip(
            frame, output_dir, prefix, duration, fps, motion, width, height
        )


comfyui_client = ComfyUIClient()
