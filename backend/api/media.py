from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config import get_settings

router = APIRouter(prefix="/media", tags=["media"])
settings = get_settings()


def _find_file(category: str, name: str) -> Path:
    dirs = {
        "character": settings.characters_dir,
        "character-variant": settings.character_variants_dir,
        "character-library": settings.character_library_dir,
        "keyframe": settings.keyframes_dir,
        "shot": settings.shots_dir,
    }
    root = dirs.get(category)
    if not root:
        raise HTTPException(404, "Invalid category")
    for path in root.rglob(name):
        if path.is_file():
            return path
    direct = root / name
    if direct.is_file():
        return direct
    raise HTTPException(404, "File not found")


@router.get("/music/{filename}")
async def get_music_file(filename: str):
    path = settings.music_dir / filename
    if not path.is_file():
        raise HTTPException(404, "Audio not found")
    return FileResponse(path)


@router.get("/mv-keyframe/{mv_id}/{filename}")
async def get_mv_keyframe(mv_id: str, filename: str):
    path = settings.mv_keyframes_dir / mv_id / filename
    if not path.is_file():
        raise HTTPException(404, "Keyframe not found")
    return FileResponse(path)


@router.get("/mv-clip/{mv_id}/{filename}")
async def get_mv_clip(mv_id: str, filename: str):
    path = settings.mv_clips_dir / mv_id / filename
    if not path.is_file():
        raise HTTPException(404, "Clip not found")
    return FileResponse(path)


@router.get("/mv-final/{mv_id}/{filename}")
async def get_mv_final(mv_id: str, filename: str):
    path = settings.mv_outputs_dir / mv_id / filename
    if not path.is_file():
        raise HTTPException(404, "MV not found")
    return FileResponse(path, media_type="video/mp4")


@router.get("/{category}/{name}")
async def get_media(category: str, name: str):
    path = _find_file(category, name)
    return FileResponse(path)


@router.get("/final/{project_id}/{filename}")
async def get_final_video(project_id: str, filename: str):
    path = settings.outputs_dir / project_id / filename
    if not path.is_file():
        raise HTTPException(404, "Video not found")
    return FileResponse(path, media_type="video/mp4")
