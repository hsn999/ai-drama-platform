from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.writer_agent import parse_story
from api.websocket import broadcast_progress
from database import AsyncSessionLocal, get_db
from models.entities import Project, Scene, Shot, Task
from schemas import (
    GenerateRequest,
    GenerateResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
    ShotResponse,
    SceneResponse,
    CharacterResponse,
    ExtractCharactersRequest,
    TaskResponse,
)
from hardware_profiles import get_profile
from services.pipeline import run_generation_pipeline

router = APIRouter(prefix="/project", tags=["project"])


async def _get_project_detail(db: AsyncSession, project_id: str) -> Project:
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.characters),
            selectinload(Project.scenes).selectinload(Scene.shots),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("/create", response_model=ProjectResponse)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(title=body.title, story=body.story, style=body.style)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/list", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await _get_project_detail(db, project_id)
    shots: list[Shot] = []
    for scene in project.scenes:
        shots.extend(sorted(scene.shots, key=lambda s: s.shot_index))
    return ProjectDetailResponse(
        id=project.id,
        title=project.title,
        story=project.story,
        style=project.style,
        status=project.status,
        output_url=project.output_url,
        config=project.config,
        created_at=project.created_at,
        updated_at=project.updated_at,
        characters=[CharacterResponse.model_validate(c) for c in project.characters],
        scenes=[SceneResponse.model_validate(s) for s in project.scenes],
        shots=[ShotResponse.model_validate(s) for s in shots],
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, body: ProjectUpdate, db: AsyncSession = Depends(get_db)
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    await db.delete(project)
    return {"ok": True}


async def _run_pipeline_bg(
    project_id: str, task_id: str, shot_count: int, hardware_profile_id: str | None
) -> None:
    async with AsyncSessionLocal() as db:
        async def on_progress(step: str, current: int, total: int, message: str) -> None:
            await broadcast_progress(project_id, step, current, total, message)

        await run_generation_pipeline(
            db, project_id, task_id, shot_count, hardware_profile_id, on_progress
        )
        await db.commit()


@router.post("/{project_id}/generate", response_model=GenerateResponse)
async def generate_project(
    project_id: str,
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    task = Task(
        project_id=project_id,
        type="video_merge",
        status="pending",
        payload=body.model_dump(),
    )
    db.add(task)
    await db.flush()

    shot_count = body.shot_count
    profile = get_profile(body.hardware_profile_id)
    if shot_count is None:
        shot_count = profile.default_shot_count
    shot_count = min(shot_count, profile.max_shot_count)

    background_tasks.add_task(
        _run_pipeline_bg, project_id, task.id, shot_count, body.hardware_profile_id
    )

    return GenerateResponse(
        task_id=task.id,
        status="pending",
        message=f"Generation started ({profile.name}, {shot_count} shots)",
    )


@router.post("/{project_id}/extract-characters")
async def extract_characters(
    project_id: str,
    body: ExtractCharactersRequest,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    parsed = await parse_story(project.story)
    profiles = parsed.get("characters_profile", [])
    generate_tasks = []
    if body.auto_generate and profiles:
        from services.pipeline import run_character_generation

        for profile in profiles:
            task = Task(project_id=project_id, type="character_gen", status="pending")
            db.add(task)
            await db.flush()
            generate_tasks.append(task.id)
            asyncio.create_task(
                _run_character_bg(
                    task.id,
                    profile.get("name", "??"),
                    profile.get("appearance", ""),
                    project.style,
                    body.variant_count,
                    project_id,
                )
            )
    return {"profiles": profiles, "generate_tasks": generate_tasks}


async def _run_character_bg(
    task_id: str, name: str, description: str, style: str, count: int, project_id: str
) -> None:
    from services.pipeline import run_character_generation

    async with AsyncSessionLocal() as db:
        await run_character_generation(db, task_id, name, description, style, count, project_id)
        await db.commit()


@router.get("/{project_id}/progress")
async def project_progress(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.created_at.desc())
    )
    task = result.scalars().first()
    if not task:
        return {"status": "idle", "progress": 0}
    return TaskResponse.model_validate(task)
