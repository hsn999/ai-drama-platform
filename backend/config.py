from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-me"

    database_url: str = f"sqlite+aiosqlite:///{ROOT_DIR / 'storage' / 'ai_drama.db'}"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_timeout: float = 120.0

    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_timeout: float = 300.0
    comfyui_output_dir: Path | None = None
    flux_unet: str = "flux1-dev-fp8.safetensors"
    flux_clip_l: str = "clip_l.safetensors"
    flux_clip_t5: str = "t5xxl_fp8_e4m3fn.safetensors"
    flux_vae: str = "ae.safetensors"

    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"

    storage_root: Path = ROOT_DIR / "storage"
    default_shot_duration: int = 5
    default_fps: int = 24
    default_resolution: str = "768x1344"
    default_output_resolution: str = "1080x1920"
    character_variant_count: int = 4
    mvp_shot_count: int = 3

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def characters_dir(self) -> Path:
        return self.storage_root / "characters"

    @property
    def character_library_dir(self) -> Path:
        return self.storage_root / "character_library"

    @property
    def character_variants_dir(self) -> Path:
        return self.storage_root / "character_variants"

    @property
    def keyframes_dir(self) -> Path:
        return self.storage_root / "keyframes"

    @property
    def shots_dir(self) -> Path:
        return self.storage_root / "shots"

    @property
    def outputs_dir(self) -> Path:
        return self.storage_root / "outputs"

    @property
    def music_dir(self) -> Path:
        return self.storage_root / "music"

    @property
    def mv_keyframes_dir(self) -> Path:
        return self.storage_root / "mv" / "keyframes"

    @property
    def mv_clips_dir(self) -> Path:
        return self.storage_root / "mv" / "clips"

    @property
    def mv_outputs_dir(self) -> Path:
        return self.storage_root / "mv" / "outputs"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for d in (
        settings.storage_root,
        settings.characters_dir,
        settings.character_library_dir,
        settings.character_variants_dir,
        settings.keyframes_dir,
        settings.shots_dir,
        settings.outputs_dir,
        settings.music_dir,
        settings.mv_keyframes_dir,
        settings.mv_clips_dir,
        settings.mv_outputs_dir,
    ):
        d.mkdir(parents=True, exist_ok=True)
    return settings
