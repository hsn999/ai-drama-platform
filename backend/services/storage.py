from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from typing import Optional

from fastapi import UploadFile

from config import get_settings

settings = get_settings()


def media_url(category: str, resource_id: str) -> str:
    return f"/api/media/{category}/{resource_id}"


def save_upload(file: UploadFile, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload.bin").suffix or ".png"
    path = directory / f"{uuid.uuid4().hex}{suffix}"
    with path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return path


def resolve_media_path(category: str, resource_id: str) -> Optional[Path]:
    roots = {
        "character": settings.characters_dir,
        "character-variant": settings.character_variants_dir,
        "character-library": settings.character_library_dir,
        "keyframe": settings.keyframes_dir,
        "shot": settings.shots_dir,
        "final": settings.outputs_dir,
        "music": settings.music_dir,
        "mv-keyframe": settings.mv_keyframes_dir,
        "mv-clip": settings.mv_clips_dir,
    }
    root = roots.get(category)
    if not root:
        return None
    for path in root.rglob(f"*{resource_id}*"):
        if path.is_file():
            return path
    candidate = root / resource_id
    if candidate.is_file():
        return candidate
    return None
