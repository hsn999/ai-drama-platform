from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    story: Mapped[str] = mapped_column(Text, nullable=False)
    style: Mapped[str] = mapped_column(String(100), default="cinematic")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    output_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    characters: Mapped[List["Character"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    scenes: Mapped[List["Scene"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    variants: Mapped[List["CharacterVariant"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class CharacterLibrary(Base):
    __tablename__ = "character_library"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    age: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    appearance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personality: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    costume: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    style: Mapped[str] = mapped_column(String(100), default="cinematic")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="generated")
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lora_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project_characters: Mapped[List["Character"]] = relationship(back_populates="library_entry")


class CharacterVariant(Base):
    __tablename__ = "character_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    library_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("character_library.id"), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Optional["Project"]] = relationship(back_populates="variants")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    library_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("character_library.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="upload")
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lora_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="characters")
    library_entry: Mapped[Optional["CharacterLibrary"]] = relationship(back_populates="project_characters")


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    scene_index: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    environment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="scenes")
    shots: Mapped[List["Shot"]] = relationship(back_populates="scene", cascade="all, delete-orphan")


class Shot(Base):
    __tablename__ = "shots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scene_id: Mapped[str] = mapped_column(String(36), ForeignKey("scenes.id"), nullable=False)
    shot_index: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=5)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    negative_prompt: Mapped[str] = mapped_column(
        Text, default="blurry, low quality, deformed"
    )
    camera_motion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    keyframe_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    scene: Mapped["Scene"] = relationship(back_populates="shots")


class MusicTrack(Base):
    __tablename__ = "music_tracks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    artist: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    audio_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lyrics_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lrc_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mv_projects: Mapped[List["MvProject"]] = relationship(
        back_populates="music_track", cascade="all, delete-orphan"
    )


class MvProject(Base):
    __tablename__ = "mv_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    music_track_id: Mapped[str] = mapped_column(String(36), ForeignKey("music_tracks.id"), nullable=False)
    style: Mapped[str] = mapped_column(String(100), default="mv_lyric_pop")
    theme: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    output_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    music_track: Mapped["MusicTrack"] = relationship(back_populates="mv_projects")
    sections: Mapped[List["MvSection"]] = relationship(
        back_populates="mv_project", cascade="all, delete-orphan"
    )
    shots: Mapped[List["MvShot"]] = relationship(
        back_populates="mv_project", cascade="all, delete-orphan"
    )


class MvSection(Base):
    __tablename__ = "mv_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    mv_project_id: Mapped[str] = mapped_column(String(36), ForeignKey("mv_projects.id"), nullable=False)
    section_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    energy: Mapped[float] = mapped_column(Float, default=0.5)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    mv_project: Mapped["MvProject"] = relationship(back_populates="sections")


class MvShot(Base):
    __tablename__ = "mv_shots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    mv_project_id: Mapped[str] = mapped_column(String(36), ForeignKey("mv_projects.id"), nullable=False)
    section_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("mv_sections.id"), nullable=True)
    shot_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    lyric_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visual_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    negative_prompt: Mapped[str] = mapped_column(
        Text, default="blurry, low quality, text, watermark, logo"
    )
    camera_motion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    keyframe_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clip_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    mv_project: Mapped["MvProject"] = relationship(back_populates="shots")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    project: Mapped[Optional["Project"]] = relationship(back_populates="tasks")
