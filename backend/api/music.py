from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audio.analyzer import probe_audio_duration
from config import get_settings
from database import get_db
from models.entities import MusicTrack
from schemas import MusicTrackResponse
from services.storage import save_upload

router = APIRouter(prefix="/music", tags=["music"])
settings = get_settings()


def _track_response(track: MusicTrack) -> MusicTrackResponse:
    return MusicTrackResponse(
        id=track.id,
        title=track.title,
        artist=track.artist,
        audio_url=f"/api/media/music/{track.audio_filename}",
        duration_sec=track.duration_sec,
        lyrics_text=track.lyrics_text,
        has_lrc=bool(track.lrc_text),
        created_at=track.created_at,
    )


@router.post("/upload", response_model=MusicTrackResponse)
async def upload_music(
    file: UploadFile = File(...),
    title: str = Form(...),
    artist: str = Form(""),
    lyrics_text: str = Form(""),
    lrc_text: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    suffix = Path(file.filename or "track.mp3").suffix.lower()
    if suffix not in (".mp3", ".wav", ".m4a", ".flac", ".ogg"):
        raise HTTPException(400, "仅支持 mp3/wav/m4a/flac/ogg")

    track_id = str(uuid.uuid4())
    filename = f"{track_id}{suffix}"
    dest = settings.music_dir / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    dest.write_bytes(content)

    duration = None
    try:
        duration = probe_audio_duration(dest)
    except Exception:
        pass

    track = MusicTrack(
        id=track_id,
        title=title.strip(),
        artist=artist.strip() or None,
        audio_filename=filename,
        duration_sec=duration,
        lyrics_text=lyrics_text.strip() or None,
        lrc_text=lrc_text.strip() or None,
    )
    db.add(track)
    await db.flush()
    await db.refresh(track)
    return _track_response(track)


@router.get("/list", response_model=list[MusicTrackResponse])
async def list_music(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MusicTrack).order_by(MusicTrack.created_at.desc()))
    return [_track_response(t) for t in result.scalars().all()]


@router.get("/{track_id}", response_model=MusicTrackResponse)
async def get_music(track_id: str, db: AsyncSession = Depends(get_db)):
    track = await db.get(MusicTrack, track_id)
    if not track:
        raise HTTPException(404, "Track not found")
    return _track_response(track)
