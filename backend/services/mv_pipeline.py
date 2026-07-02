from __future__ import annotations

from typing import Awaitable, Callable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.mv_director_agent import finalize_shot_prompt, plan_mv_shots
from api.websocket import broadcast_progress
from audio.analyzer import (
    build_sections_from_lyrics,
    distribute_lyric_lines,
    parse_lrc,
    probe_audio_duration,
)
from comfyui.api import comfyui_client
from config import get_settings
from hardware_profiles import get_profile
from models.entities import MusicTrack, MvProject, MvSection, MvShot, Task
from mv_styles import get_mv_style
from services.storage import media_url
from video.ffmpeg import concat_videos, image_to_kenburns_clip, mux_mv_final
from video.subtitles import build_ass_from_shots

settings = get_settings()

ProgressCallback = Callable[[str, int, int, str], Awaitable[None]]

MOTIONS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]


async def run_mv_pipeline(
    db: AsyncSession,
    mv_project_id: str,
    task_id: str,
    *,
    shot_count: Optional[int] = None,
    hardware_profile_id: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> None:
    profile = get_profile(hardware_profile_id)
    llm_model = profile.ollama_model
    style = get_mv_style()

    async def progress(step: str, current: int, total: int, message: str) -> None:
        task = await db.get(Task, task_id)
        if task:
            task.progress = int(current / total * 100) if total else 0
            await db.flush()
        if on_progress:
            await on_progress(step, current, total, message)

    task = await db.get(Task, task_id)
    result = await db.execute(
        select(MvProject)
        .where(MvProject.id == mv_project_id)
        .options(
            selectinload(MvProject.music_track),
            selectinload(MvProject.sections),
            selectinload(MvProject.shots),
        )
    )
    mv = result.scalar_one_or_none()
    if not task or not mv or not mv.music_track:
        return

    track = mv.music_track
    audio_path = settings.music_dir / track.audio_filename

    try:
        task.status = "running"
        mv.status = "analyzing"
        await db.flush()

        await progress("audio_analyze", 0, 6, "分析音频与歌词...")
        duration = track.duration_sec
        if not duration and audio_path.is_file():
            duration = probe_audio_duration(audio_path)
            track.duration_sec = duration
        duration = duration or 180.0

        lyric_lines: list[dict] = []
        if track.lrc_text:
            lyric_lines = parse_lrc(track.lrc_text)
            for ln in lyric_lines:
                if ln.get("end_sec") is None:
                    ln["end_sec"] = duration
        elif track.lyrics_text:
            lyric_lines = distribute_lyric_lines(track.lyrics_text, duration)

        sections_data = build_sections_from_lyrics(lyric_lines, duration)
        target_shots = shot_count or min(20, max(12, int(duration / 5)))

        for old in list(mv.sections):
            await db.delete(old)
        for old in list(mv.shots):
            await db.delete(old)
        await db.flush()

        await progress("mv_director", 1, 6, "MV 导演分镜规划...")
        mv.status = "planning"
        shots_data = await plan_mv_shots(
            duration_sec=duration,
            sections=sections_data,
            lyric_lines=lyric_lines,
            theme=mv.theme or track.title,
            style_id=mv.style,
            target_shots=target_shots,
            ollama_model=llm_model,
        )

        sections: List[MvSection] = []
        for i, sec in enumerate(sections_data):
            section = MvSection(
                mv_project_id=mv.id,
                section_index=i + 1,
                section_type=sec["type"],
                start_sec=float(sec["start_sec"]),
                end_sec=float(sec["end_sec"]),
                energy=float(sec.get("energy", 0.5)),
                metadata_={"lyric_lines": sec.get("lyric_lines", [])},
            )
            db.add(section)
            sections.append(section)
        await db.flush()

        def _find_section(start: float) -> Optional[MvSection]:
            for sec in sections:
                if sec.start_sec <= start < sec.end_sec:
                    return sec
            return sections[0] if sections else None

        shots: List[MvShot] = []
        for item in shots_data:
            start = float(item.get("start_sec", 0))
            end = float(item.get("end_sec", start + 5))
            section = _find_section(start)
            shot = MvShot(
                mv_project_id=mv.id,
                section_id=section.id if section else None,
                shot_index=int(item.get("shot_index", len(shots) + 1)),
                start_sec=start,
                end_sec=end,
                duration_sec=max(end - start, 0.5),
                lyric_text=item.get("lyric_text"),
                visual_prompt=item.get("visual_prompt"),
                camera_motion=item.get("camera_motion"),
                metadata_={"emotion": item.get("emotion"), "raw": item},
            )
            db.add(shot)
            shots.append(shot)
        await db.flush()

        await progress("prompt_gen", 2, 6, "优化画面 Prompt...")
        mv.status = "generating"
        for shot in shots:
            raw = shot.visual_prompt or "emotional vertical music video scene"
            shot.visual_prompt = finalize_shot_prompt(raw, mv.style)
        await db.flush()

        out_w, out_h = map(int, style.output_resolution.split("x"))
        gen_w, gen_h = map(int, style.gen_resolution.split("x"))
        keyframe_dir = settings.mv_keyframes_dir / mv.id
        clip_dir = settings.mv_clips_dir / mv.id
        clip_paths: List[str] = []
        total = len(shots)

        for i, shot in enumerate(shots):
            await progress("keyframe_generate", i, total, f"生成镜头 {i + 1}/{total}...")
            shot.status = "generating"
            await db.flush()

            img_path = await comfyui_client.generate_image(
                shot.visual_prompt or "",
                keyframe_dir,
                prefix=f"shot{shot.shot_index:03d}",
                width=gen_w,
                height=gen_h,
                checkpoint=profile.comfyui_checkpoint,
                sampler_steps=profile.sampler_steps,
            )
            shot.keyframe_url = media_url("mv-keyframe", f"{mv.id}/{img_path.name}")

            motion = MOTIONS[(shot.shot_index - 1) % len(MOTIONS)]
            if shot.camera_motion and "zoom" in shot.camera_motion.lower():
                motion = "zoom_in"
            clip_path = clip_dir / f"shot_{shot.shot_index:03d}.mp4"
            await image_to_kenburns_clip(
                str(img_path),
                str(clip_path),
                shot.duration_sec,
                resolution=style.output_resolution,
                fps=settings.default_fps,
                motion=motion,
            )
            shot.clip_url = media_url("mv-clip", f"{mv.id}/{clip_path.name}")
            shot.status = "completed"
            clip_paths.append(str(clip_path))
            await db.flush()

        await progress("video_compose", total, total, "合成视频轨...")
        mv.status = "composing"
        compose_dir = settings.mv_outputs_dir / mv.id
        compose_dir.mkdir(parents=True, exist_ok=True)
        silent_video = str(compose_dir / "silent.mp4")
        await concat_videos(clip_paths, silent_video)

        shot_dicts = [
            {
                "start_sec": s.start_sec,
                "end_sec": s.end_sec,
                "lyric_text": s.lyric_text,
            }
            for s in shots
        ]
        ass_path = compose_dir / "lyrics.ass"
        ass_path.write_text(
            build_ass_from_shots(shot_dicts, width=out_w, height=out_h),
            encoding="utf-8-sig",
        )

        await progress("mux_subtitle", 5, 6, "混流原曲 + 烧录歌词...")
        final_path = compose_dir / "final.mp4"
        await mux_mv_final(
            silent_video,
            str(audio_path),
            str(ass_path),
            str(final_path),
        )

        mv.output_url = f"/api/media/mv-final/{mv.id}/final.mp4"
        mv.status = "completed"
        task.status = "completed"
        task.progress = 100
        task.result = {"output_url": mv.output_url}
        await db.flush()

        await progress("done", 6, 6, "竖屏歌词 MV 生成完成")

    except Exception as exc:
        mv.status = "failed"
        task.status = "failed"
        task.result = {"error": str(exc)}
        await db.flush()
        raise
