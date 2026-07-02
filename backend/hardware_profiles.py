from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from config import ROOT_DIR

CONFIG_PATH = ROOT_DIR / "storage" / "system_config.json"


@dataclass(frozen=True)
class HardwareProfile:
    id: str
    name: str
    gpu_model: str
    vram_gb: int
    ram_gb: int
    ollama_model: str
    default_resolution: str
    default_output_resolution: str
    default_shot_count: int
    max_shot_count: int
    character_variant_count: int
    comfyui_checkpoint: str
    comfyui_fp16: bool
    comfyui_lowvram: bool
    sampler_steps: int
    description: str
    cloud_tips: str

    @property
    def width(self) -> int:
        return int(self.default_resolution.split("x")[0])

    @property
    def height(self) -> int:
        return int(self.default_resolution.split("x")[1])

    def to_dict(self) -> dict:
        return asdict(self)


PROFILES: dict[str, HardwareProfile] = {
    "rtx5060ti_16g": HardwareProfile(
        id="rtx5060ti_16g",
        name="RTX 5060 Ti · 16G 显存",
        gpu_model="RTX 5060 Ti",
        vram_gb=16,
        ram_gb=32,
        ollama_model="qwen3:8b",
        default_resolution="768x1344",
        default_output_resolution="1080x1920",
        default_shot_count=3,
        max_shot_count=6,
        character_variant_count=4,
        comfyui_checkpoint="flux1-dev-fp8.safetensors",
        comfyui_fp16=True,
        comfyui_lowvram=False,
        sampler_steps=20,
        description="新架构显卡，16G 显存。推荐 Flux 量化版，分镜用 8b，与 ComfyUI 串行渲染。",
        cloud_tips="恒源云/AutoDL 选 RTX 5060 Ti 16G + 32G 内存；模型用 NF4/GGUF 量化 Flux。",
    ),
    "rtx2080ti_22g": HardwareProfile(
        id="rtx2080ti_22g",
        name="RTX 2080 Ti · 22G 显存",
        gpu_model="RTX 2080 Ti",
        vram_gb=22,
        ram_gb=32,
        ollama_model="qwen3:14b",
        default_resolution="768x1344",
        default_output_resolution="1080x1920",
        default_shot_count=6,
        max_shot_count=12,
        character_variant_count=4,
        comfyui_checkpoint="flux1-dev.safetensors",
        comfyui_fp16=True,
        comfyui_lowvram=False,
        sampler_steps=24,
        description="显存更大（22G），可用 14b 分镜、更多镜头。架构较老，优先 FP16 全量或轻度量化 Flux。",
        cloud_tips="租用平台选 2080 Ti 22G + 32G 内存；可尝试 6~12 镜，分镜后记得 ollama stop 再渲染。",
    ),
}

DEFAULT_PROFILE_ID = "rtx5060ti_16g"


def list_profiles() -> list[dict]:
    return [p.to_dict() for p in PROFILES.values()]


def get_profile(profile_id: Optional[str] = None) -> HardwareProfile:
    pid = profile_id or get_active_profile_id()
    if pid not in PROFILES:
        pid = DEFAULT_PROFILE_ID
    return PROFILES[pid]


def get_active_profile_id() -> str:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            pid = data.get("hardware_profile_id", DEFAULT_PROFILE_ID)
            if pid in PROFILES:
                return pid
        except (json.JSONDecodeError, OSError):
            pass
    env_pid = os.environ.get("HARDWARE_PROFILE_ID", "").strip()
    if env_pid in PROFILES:
        return env_pid
    return DEFAULT_PROFILE_ID


def set_active_profile_id(profile_id: str) -> HardwareProfile:
    if profile_id not in PROFILES:
        raise ValueError(f"Unknown hardware profile: {profile_id}")
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps({"hardware_profile_id": profile_id}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return PROFILES[profile_id]
