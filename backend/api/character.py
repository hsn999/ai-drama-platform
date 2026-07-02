from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, get_db
from models.entities import Character, CharacterLibrary, CharacterVariant, Project, Task
from schemas import (
    CharacterFromLibraryRequest,
    CharacterGenerateRequest,
    CharacterResponse,
    CharacterSelectVariantRequest,
)
from services.pipeline import run_character_generation
from services.storage import media_url, save_upload
from config import get_settings

router = APIRouter(prefix="/character", tags=["character"])
settings = get_settings()


@router.post("/upload", response_model=CharacterResponse)
async def upload_character(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    save_to_library: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    path = save_upload(file, settings.characters_dir / project_id)
    image_url = f"/api/media/character/{path.name}"

    character = Character(
        project_id=project_id,
        name=name,
        description=description,
        image_url=image_url,
        source="upload",
    )
    db.add(character)

    if save_to_library:
        lib = CharacterLibrary(
            name=name,
            description=description,
            image_url=image_url,
            source="upload",
        )
        db.add(lib)
        await db.flush()
        character.library_id = lib.id

    await db.flush()
    await db.refresh(character)
    return character


@router.post("/generate")
async def generate_character(body: CharacterGenerateRequest, db: AsyncSession = Depends(get_db)):
    task = Task(
        project_id=body.project_id,
        type="character_gen",
        status="pending",
        payload=body.model_dump(),
    )
    db.add(task)
    await db.flush()

    asyncio.create_task(
        _run_character_task(
            task.id,
            body.name,
            body.description,
            body.style,
            body.variant_count,
            body.project_id,
        )
    )
    return {"task_id": task.id, "status": "pending", "message": "character generation queued"}


async def _run_character_task(
    task_id: str, name: str, description: str, style: str, count: int, project_id: str
) -> None:
    async with AsyncSessionLocal() as db:
        await run_character_generation(db, task_id, name, description, style, count, project_id)
        await db.commit()


@router.post("/select-variant", response_model=CharacterResponse)
async def select_variant(body: CharacterSelectVariantRequest, db: AsyncSession = Depends(get_db)):
    variant = await db.get(CharacterVariant, body.variant_id)
    if not variant:
        raise HTTPException(404, "Variant not found")

    variant.is_selected = True
    library_id = None
    if body.save_to_library:
        lib = CharacterLibrary(
            name=body.name,
            image_url=variant.image_url,
            generation_prompt=variant.prompt,
            source="generated",
            tags=body.tags,
        )
        db.add(lib)
        await db.flush()
        library_id = lib.id

    character = Character(
        project_id=body.project_id,
        library_id=library_id,
        name=body.name,
        image_url=variant.image_url,
        source="generated" if not library_id else "library",
        generation_prompt=variant.prompt,
    )
    db.add(character)
    await db.flush()
    await db.refresh(character)
    return character


@router.post("/from-library", response_model=CharacterResponse)
async def from_library(body: CharacterFromLibraryRequest, db: AsyncSession = Depends(get_db)):
    lib = await db.get(CharacterLibrary, body.library_id)
    if not lib or lib.is_deleted:
        raise HTTPException(404, "Library character not found")

    character = Character(
        project_id=body.project_id,
        library_id=lib.id,
        name=body.name or lib.name,
        image_url=lib.image_url,
        description=lib.description,
        source="library",
    )
    db.add(character)
    await db.flush()
    await db.refresh(character)
    return character


@router.get("/list", response_model=list[CharacterResponse])
async def list_characters(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Character).where(Character.project_id == project_id))
    return result.scalars().all()


@router.delete("/{character_id}")
async def delete_character(character_id: str, db: AsyncSession = Depends(get_db)):
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(404, "Character not found")
    await db.delete(character)
    return {"ok": True}
