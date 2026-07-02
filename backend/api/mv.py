from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.websocket import broadcast_progress
from database import AsyncSessionLocal, get_db
from hardware_profiles import get_profile
from models.entities import MusicTrack, MvProject, MvShot, Task
from mv_styles import PRESETS
from schemas import (
    GenerateResponse,
    MvCreateRequest,
    MvGenerateRequest,
    MvProjectDetailResponse,
    MvProjectResponse,
    MvSectionResponse,
    MvShotResponse,
    MvStyleResponse,
    MvUpdateRequest,
    MusicTrackResponse,
    TaskResponse,
)
from services.mv_pipeline import run_mv_pipeline

router = APIRouter(prefix="/mv", tags=["mv"])


def _music_response(track: MusicTrack) -> MusicTrackResponse:
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


async def _get_mv_detail(db: AsyncSession, mv_id: str) -> MvProject:
    result = await db.execute(
        select(MvProject)
        .where(MvProject.id == mv_id)
        .options(
            selectinload(MvProject.music_track),
            selectinload(MvProject.sections),
            selectinload(MvProject.shots),
        )
    )
    mv = result.scalar_one_or_none()
    if not mv:
        raise HTTPException(404, "MV project not found")
    return mv


def _mv_detail(mv: MvProject) -> MvProjectDetailResponse:
    shots = sorted(mv.shots, key=lambda s: s.shot_index)
    sections = sorted(mv.sections, key=lambda s: s.section_index)
    return MvProjectDetailResponse(
        id=mv.id,
        title=mv.title,
        music_track_id=mv.music_track_id,
        style=mv.style,
        theme=mv.theme,
        status=mv.status,
        output_url=mv.output_url,
        created_at=mv.created_at,
        updated_at=mv.updated_at,
        music_track=_music_response(mv.music_track) if mv.music_track else None,
        sections=[MvSectionResponse.model_validate(s) for s in sections],
        shots=[MvShotResponse.model_validate(s) for s in shots],
    )


@router.get("/styles", response_model=list[MvStyleResponse])
async def list_mv_styles():
    return [
        MvStyleResponse(
            id=p.id,
            name=p.name,
            aspect_ratio=p.aspect_ratio,
            output_resolution=p.output_resolution,
            description=p.description,
        )
        for p in PRESETS.values()
    ]


@router.post("/create", response_model=MvProjectResponse)
async def create_mv(body: MvCreateRequest, db: AsyncSession = Depends(get_db)):
    track = await db.get(MusicTrack, body.music_track_id)
    if not track:
        raise HTTPException(404, "Music track not found")

    mv = MvProject(
        title=body.title or f"{track.title} · 歌词MV",
        music_track_id=track.id,
        style=body.style,
        theme=body.theme,
        status="draft",
    )
    db.add(mv)
    await db.flush()
    await db.refresh(mv)
    return mv


@router.get("/list", response_model=list[MvProjectResponse])
async def list_mv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MvProject).order_by(MvProject.created_at.desc()))
    return result.scalars().all()


@router.get("/{mv_id}", response_model=MvProjectDetailResponse)
async def get_mv(mv_id: str, db: AsyncSession = Depends(get_db)):
    mv = await _get_mv_detail(db, mv_id)
    return _mv_detail(mv)


@router.put("/{mv_id}", response_model=MvProjectResponse)
async def update_mv(mv_id: str, body: MvUpdateRequest, db: AsyncSession = Depends(get_db)):
    mv = await db.get(MvProject, mv_id)
    if not mv:
        raise HTTPException(404, "MV project not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(mv, field, value)
    await db.flush()
    await db.refresh(mv)
    return mv


async def _run_mv_bg(
    mv_id: str, task_id: str, shot_count: int | None, hardware_profile_id: str | None
) -> None:
    async with AsyncSessionLocal() as db:
        async def on_progress(step: str, current: int, total: int, message: str) -> None:
            await broadcast_progress(mv_id, step, current, total, message)

        await run_mv_pipeline(
            db, mv_id, task_id, shot_count=shot_count,
            hardware_profile_id=hardware_profile_id, on_progress=on_progress,
        )
        await db.commit()


@router.post("/{mv_id}/generate", response_model=GenerateResponse)
async def generate_mv(
    mv_id: str,
    body: MvGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    mv = await db.get(MvProject, mv_id)
    if not mv:
        raise HTTPException(404, "MV project not found")
    if mv.status in ("generating", "queued", "analyzing", "planning", "composing"):
        raise HTTPException(409, "MV is already generating")

    profile = get_profile(body.hardware_profile_id)
    shot_count = body.shot_count
    if shot_count is not None:
        shot_count = min(max(shot_count, 8), 24)

    task = Task(
        project_id=None,
        type="mv_generate",
        status="pending",
        payload={"mv_project_id": mv_id, **body.model_dump()},
    )
    db.add(task)
    mv.status = "queued"
    await db.flush()

    background_tasks.add_task(_run_mv_bg, mv_id, task.id, shot_count, body.hardware_profile_id)

    return GenerateResponse(
        task_id=task.id,
        status="pending",
        message=f"竖屏歌词 MV 生成已启动（{profile.name}）",
    )


@router.get("/{mv_id}/progress")
async def mv_progress(mv_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .where(Task.type == "mv_generate")
        .order_by(Task.created_at.desc())
    )
    for task in result.scalars().all():
        if task.payload and task.payload.get("mv_project_id") == mv_id:
            return TaskResponse.model_validate(task)
    return {"status": "idle", "progress": 0}
