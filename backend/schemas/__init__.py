from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str
    story: str
    style: str = "cinematic"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    story: Optional[str] = None
    style: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    story: str
    style: str
    status: str
    output_url: Optional[str] = None
    config: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    shot_count: Optional[int] = None
    resolution: Optional[str] = None
    enable_bgm: bool = False
    hardware_profile_id: Optional[str] = None


class HardwareProfileResponse(BaseModel):
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


class HardwareProfileSelectRequest(BaseModel):
    profile_id: str


class GenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str


class CharacterResponse(BaseModel):
    id: str
    project_id: str
    library_id: Optional[str] = None
    name: str
    image_url: str
    description: Optional[str] = None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CharacterGenerateRequest(BaseModel):
    project_id: str
    name: str
    description: str
    style: str = "cinematic"
    variant_count: int = 4
    save_to_library: bool = False


class CharacterSelectVariantRequest(BaseModel):
    variant_id: str
    project_id: str
    name: str
    save_to_library: bool = False
    tags: List[str] = Field(default_factory=list)


class CharacterFromLibraryRequest(BaseModel):
    project_id: str
    library_id: str
    name: Optional[str] = None


class LibraryCharacterCreate(BaseModel):
    name: str
    description: Optional[str] = None
    appearance: Optional[str] = None
    style: str = "cinematic"
    tags: List[str] = Field(default_factory=list)
    image_url: str
    source: str = "upload"


class LibraryCharacterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    appearance: Optional[str] = None
    style: Optional[str] = None
    tags: Optional[List[str]] = None


class LibraryCharacterResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    appearance: Optional[str] = None
    style: str
    tags: List[str]
    image_url: str
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExtractCharactersRequest(BaseModel):
    auto_generate: bool = False
    variant_count: int = 4


class SceneResponse(BaseModel):
    id: str
    scene_index: int
    description: Optional[str] = None
    emotion: Optional[str] = None
    environment: Optional[str] = None

    model_config = {"from_attributes": True}


class ShotResponse(BaseModel):
    id: str
    shot_index: int
    duration: int
    prompt: Optional[str] = None
    camera_motion: Optional[str] = None
    status: str
    keyframe_url: Optional[str] = None
    video_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectDetailResponse(ProjectResponse):
    characters: List[CharacterResponse] = Field(default_factory=list)
    scenes: List[SceneResponse] = Field(default_factory=list)
    shots: List[ShotResponse] = Field(default_factory=list)


class TaskResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    type: str
    status: str
    payload: Optional[dict] = None
    result: Optional[dict] = None
    progress: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgressMessage(BaseModel):
    type: str = "progress"
    step: str
    current: int = 0
    total: int = 0
    shot_id: Optional[str] = None
    message: str = ""
    percent: int = 0


class MusicTrackResponse(BaseModel):
    id: str
    title: str
    artist: Optional[str] = None
    audio_url: str
    duration_sec: Optional[float] = None
    lyrics_text: Optional[str] = None
    has_lrc: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class MvStyleResponse(BaseModel):
    id: str
    name: str
    aspect_ratio: str
    output_resolution: str
    description: str


class MvCreateRequest(BaseModel):
    music_track_id: str
    title: Optional[str] = None
    theme: Optional[str] = None
    style: str = "mv_lyric_pop"


class MvUpdateRequest(BaseModel):
    title: Optional[str] = None
    theme: Optional[str] = None


class MvGenerateRequest(BaseModel):
    shot_count: Optional[int] = None
    hardware_profile_id: Optional[str] = None


class MvSectionResponse(BaseModel):
    id: str
    section_index: int
    section_type: str
    start_sec: float
    end_sec: float
    energy: float

    model_config = {"from_attributes": True}


class MvShotResponse(BaseModel):
    id: str
    shot_index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    lyric_text: Optional[str] = None
    visual_prompt: Optional[str] = None
    camera_motion: Optional[str] = None
    status: str
    keyframe_url: Optional[str] = None
    clip_url: Optional[str] = None

    model_config = {"from_attributes": True}


class MvProjectResponse(BaseModel):
    id: str
    title: str
    music_track_id: str
    style: str
    theme: Optional[str] = None
    status: str
    output_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MvProjectDetailResponse(MvProjectResponse):
    music_track: Optional[MusicTrackResponse] = None
    sections: List[MvSectionResponse] = Field(default_factory=list)
    shots: List[MvShotResponse] = Field(default_factory=list)


class CharacterVariantsReadyMessage(BaseModel):
    type: str = "character_variants_ready"
    task_id: str
    variants: List[Dict[str, Any]]
