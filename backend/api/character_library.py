from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.entities import CharacterLibrary
from schemas import LibraryCharacterCreate, LibraryCharacterResponse, LibraryCharacterUpdate

router = APIRouter(prefix="/library/characters", tags=["character-library"])


@router.get("", response_model=list[LibraryCharacterResponse])
async def list_library(
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CharacterLibrary).where(CharacterLibrary.is_deleted.is_(False))
    if keyword:
        stmt = stmt.where(
            or_(
                CharacterLibrary.name.ilike(f"%{keyword}%"),
                CharacterLibrary.appearance.ilike(f"%{keyword}%"),
            )
        )
    stmt = stmt.order_by(CharacterLibrary.updated_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{library_id}", response_model=LibraryCharacterResponse)
async def get_library_character(library_id: str, db: AsyncSession = Depends(get_db)):
    item = await db.get(CharacterLibrary, library_id)
    if not item or item.is_deleted:
        raise HTTPException(404, "Character not found")
    return item


@router.post("", response_model=LibraryCharacterResponse)
async def create_library_character(body: LibraryCharacterCreate, db: AsyncSession = Depends(get_db)):
    item = CharacterLibrary(**body.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/{library_id}", response_model=LibraryCharacterResponse)
async def update_library_character(
    library_id: str, body: LibraryCharacterUpdate, db: AsyncSession = Depends(get_db)
):
    item = await db.get(CharacterLibrary, library_id)
    if not item or item.is_deleted:
        raise HTTPException(404, "Character not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{library_id}")
async def delete_library_character(library_id: str, db: AsyncSession = Depends(get_db)):
    item = await db.get(CharacterLibrary, library_id)
    if not item:
        raise HTTPException(404, "Character not found")
    item.is_deleted = True
    return {"ok": True}
