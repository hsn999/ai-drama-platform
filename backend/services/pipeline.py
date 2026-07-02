from __future__ import annotations

import logging
from pathlib import Path
from typing import Awaitable, Callable, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.character_designer_agent import design_character_prompt
from agents.director_agent import optimize_prompt
from agents.prompt_agent import generate_shot_prompt
from agents.storyboard_agent import _fallback_shots, create_storyboard
from agents.subject_context import motion_from_camera
from agents.writer_agent import parse_story
from comfyui.api import comfyui_client
from config import get_settings
from hardware_profiles import HardwareProfile, get_profile
from models.entities import Project, Scene, Shot, Task
from video.ffmpeg import concat_videos

settings = get_settings()
logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, int, int, str], Awaitable[None]]


def _scene_payload(scene: Scene) -> dict:
    return {
        "scene": scene.scene_index,
        "description": scene.description,
        "emotion": scene.emotion,
        "environment": scene.environment,
    }


async def _load_project(db: AsyncSession, project_id: str) -> Project | None:
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.scenes).selectinload(Scene.shots))
    )
    return result.scalar_one_or_none()


async def run_generation_pipeline(
    db: AsyncSession,
    project_id: str,
    task_id: str,
    shot_count: Optional[int] = None,
    hardware_profile_id: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> None:
    profile = get_profile(hardware_profile_id)
    shot_count = shot_count or profile.default_shot_count
    shot_count = min(shot_count, profile.max_shot_count)
    llm_model = profile.ollama_model

    async def progress(step: str, current: int, total: int, message: str) -> None:
        task = await db.get(Task, task_id)
        if task:
            task.progress = int(current / total * 100) if total else 0
            await db.flush()
            await db.commit()
        if on_progress:
            await on_progress(step, current, total, message)

    task = await db.get(Task, task_id)
    project = await _load_project(db, project_id)
    if not task or not project:
        return

    try:
        task.status = "running"
        project.status = "parsing"
        await db.flush()
        await db.commit()

        await progress("story_parse", 0, 5, f"Parsing story ({profile.name})...")
        story_context = (project.story or "").strip()
        parsed = await parse_story(story_context, ollama_model=llm_model)
        scenes_data = parsed.get("scenes", [])

        await db.execute(
            delete(Shot).where(
                Shot.scene_id.in_(select(Scene.id).where(Scene.project_id == project.id))
            )
        )
        await db.execute(delete(Scene).where(Scene.project_id == project.id))
        await db.flush()

        scenes: List[Scene] = []
        for item in scenes_data:
            scene = Scene(
                project_id=project.id,
                scene_index=item.get("scene", len(scenes) + 1),
                description=item.get("description"),
                emotion=item.get("emotion"),
                environment=item.get("environment"),
            )
            db.add(scene)
            scenes.append(scene)
        await db.flush()

        await progress("storyboard", 1, 5, "Creating storyboard...")
        project.status = "storyboarding"
        shots_data = await create_storyboard(
            [_scene_payload(s) for s in scenes] if scenes else [{"description": story_context}],
            shot_count=shot_count,
            story_context=story_context,
            ollama_model=llm_model,
        )
        if not shots_data:
            logger.warning("Storyboard returned no shots, using fallback for project %s", project.id)
            shots_data = _fallback_shots(
                [_scene_payload(s) for s in scenes] if scenes else [{"description": story_context}],
                shot_count,
                story_context,
            )

        if not scenes:
            scene = Scene(project_id=project.id, scene_index=1, description=project.story)
            db.add(scene)
            await db.flush()
            scenes = [scene]

        scene = scenes[0]
        await db.flush()
        await db.execute(delete(Shot).where(Shot.scene_id == scene.id))
        await db.flush()

        shots: List[Shot] = []
        for idx, item in enumerate(shots_data):
            shot = Shot(
                scene_id=scene.id,
                shot_index=item.get("shot_index", idx + 1),
                duration=item.get("duration", settings.default_shot_duration),
                camera_motion=item.get("camera_motion"),
                metadata_={"raw": item},
            )
            db.add(shot)
            shots.append(shot)
        await db.flush()

        await progress("prompt_gen", 2, 5, "Generating prompts...")
        project.status = "generating"
        for shot in shots:
            raw = shot.metadata_.get("raw", {})
            prompt = await generate_shot_prompt(
                raw, project.style, story_context=story_context, ollama_model=llm_model
            )
            shot.prompt = await optimize_prompt(
                prompt, story_context=story_context, ollama_model=llm_model
            )
        await db.flush()

        video_paths: List[str] = []
        total = len(shots)
        for i, shot in enumerate(shots):
            await progress("video_generate", i, total, f"Generating shot {i + 1}/{total}...")
            shot.status = "generating"
            await db.flush()
            out_dir = settings.shots_dir / project.id
            video_path = await comfyui_client.generate_video_from_prompt(
                shot.prompt or "cinematic scene",
                out_dir,
                prefix=f"shot_{shot.shot_index}",
                duration=shot.duration,
                fps=settings.default_fps,
                width=profile.width,
                height=profile.height,
                checkpoint=profile.comfyui_checkpoint,
                sampler_steps=profile.sampler_steps,
                motion=motion_from_camera(shot.camera_motion),
            )
            if not video_path.is_file():
                raise RuntimeError(f"Video file not created for shot {shot.shot_index}: {video_path}")
            shot.video_url = f"/api/media/shot/{video_path.name}"
            shot.status = "completed"
            video_paths.append(str(video_path))
            await db.flush()

        video_paths = [p for p in video_paths if Path(p).is_file()]
        if not video_paths:
            raise RuntimeError(
                f"No shot videos generated (expected {len(shots)}). "
                "Check ComfyUI and ffmpeg are running."
            )

        await progress("video_merge", total, total, "Merging videos...")
        project.status = "editing"
        output_path = settings.outputs_dir / project.id / "final.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await concat_videos(video_paths, str(output_path))

        project.output_url = f"/api/media/final/{project.id}/final.mp4"
        project.status = "completed"
        task.status = "completed"
        task.progress = 100
        task.result = {
            "output_url": project.output_url,
            "shot_count": len(shots),
            "hardware_profile_id": profile.id,
            "ollama_model": llm_model,
            "resolution": profile.default_resolution,
        }
        await db.flush()

        await progress("completed", total, total, "Done")

    except Exception as exc:
        await db.rollback()
        task = await db.get(Task, task_id)
        project = await db.get(Project, project_id)
        if task and project:
            project.status = "failed"
            task.status = "failed"
            task.result = {"error": str(exc)}
            await db.commit()
        raise


async def run_character_generation(
    db: AsyncSession,
    task_id: str,
    name: str,
    description: str,
    style: str,
    variant_count: int,
    project_id: Optional[str] = None,
    hardware_profile_id: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> None:
    from models.entities import CharacterVariant

    profile = get_profile(hardware_profile_id)
    variant_count = min(variant_count, profile.character_variant_count)

    task = await db.get(Task, task_id)
    if not task:
        return

    try:
        task.status = "running"
        await db.flush()

        profile_data = {"name": name, "appearance": description}
        prompt = await design_character_prompt(profile_data, style, ollama_model=profile.ollama_model)
        out_dir = settings.character_variants_dir / task_id
        variants = []

        for i in range(variant_count):
            if on_progress:
                await on_progress("character_generate", i + 1, variant_count, f"variant {i + 1}/{variant_count}")
            img = await comfyui_client.generate_image(
                prompt,
                out_dir,
                prefix=f"variant_{i + 1}",
                width=profile.width,
                height=1024,
                checkpoint=profile.comfyui_checkpoint,
                sampler_steps=profile.sampler_steps,
            )
            variant = CharacterVariant(
                project_id=project_id,
                name=name,
                prompt=prompt,
                image_url=f"/api/media/character-variant/{img.name}",
            )
            db.add(variant)
            variants.append(variant)
        await db.flush()

        task.status = "completed"
        task.progress = 100
        task.result = {
            "variants": [{"id": v.id, "image_url": v.image_url} for v in variants],
            "prompt": prompt,
        }
        await db.flush()
    except Exception as exc:
        task.status = "failed"
        task.result = {"error": str(exc)}
        await db.flush()
        raise
