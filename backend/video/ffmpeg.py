from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from config import get_settings

settings = get_settings()


async def run_ffmpeg(args: list[str]) -> None:
    cmd = [settings.ffmpeg_path, *args]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode() or "FFmpeg failed")


async def images_to_video(image_paths: list[str], output_path: str, duration: int, fps: int) -> None:
    if not image_paths:
        raise ValueError("No images provided")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    per_image = duration / len(image_paths)
    list_file = Path(output_path).with_suffix(".txt")
    lines = []
    for img in image_paths:
        lines.append(f"file '{Path(img).as_posix()}'")
        lines.append(f"duration {per_image}")
    lines.append(f"file '{Path(image_paths[-1]).as_posix()}'")
    list_file.write_text("\n".join(lines), encoding="utf-8")
    await run_ffmpeg(
        [
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-vf",
            f"fps={fps},scale={settings.default_output_resolution.replace('x', ':')}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
    )
    list_file.unlink(missing_ok=True)


def _parse_resolution(resolution: str) -> tuple[int, int]:
    w, h = resolution.split("x")
    return int(w), int(h)


async def image_to_kenburns_clip(
    image_path: str,
    output_path: str,
    duration_sec: float,
    *,
    resolution: str = "1080x1920",
    fps: int = 24,
    motion: str = "zoom_in",
) -> None:
    width, height = _parse_resolution(resolution)
    frames = max(int(duration_sec * fps), 1)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if motion in ("zoom_out", "pull_back"):
        z_expr = "if(lte(zoom,1.0),1.2,max(1.001,zoom-0.0015))"
        z_init = "1.2"
    elif motion in ("pan_left", "pan_right"):
        z_expr = "1.08"
        z_init = "1.08"
    else:
        z_expr = "min(zoom+0.0015,1.15)"
        z_init = "1.0"
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={width}x{height}:fps={fps}"
    )
    await run_ffmpeg(
        [
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-vf",
            vf,
            "-t",
            str(duration_sec),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
    )


async def mux_audio_video(video_path: str, audio_path: str, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    await run_ffmpeg(
        [
            "-y",
            "-i",
            video_path,
            "-i",
            audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            str(output_path),
        ]
    )


def _escape_sub_path(path: Path) -> str:
    return path.resolve().as_posix().replace(":", r"\:")


async def burn_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    *,
    use_ass: bool = True,
) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sub = _escape_sub_path(Path(subtitle_path))
    style = "subtitles" if subtitle_path.endswith(".ass") or use_ass else "subtitles"
    vf = f"{style}='{sub}'"
    await run_ffmpeg(
        [
            "-y",
            "-i",
            video_path,
            "-vf",
            vf,
            "-c:a",
            "copy",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
    )


async def mux_mv_final(
    video_path: str,
    audio_path: str,
    subtitle_path: str,
    output_path: str,
) -> None:
    """混流原曲音轨并烧录 ASS 歌词字幕."""
    tmp = str(Path(output_path).with_suffix(".mux.mp4"))
    await mux_audio_video(video_path, audio_path, tmp)
    await burn_subtitles(tmp, subtitle_path, output_path, use_ass=subtitle_path.endswith(".ass"))
    Path(tmp).unlink(missing_ok=True)


async def concat_videos(video_paths: list[str], output_path: str) -> None:
    if not video_paths:
        raise ValueError("No videos provided")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    list_file = Path(output_path).with_suffix(".txt")
    list_file.write_text(
        "\n".join(f"file '{Path(v).as_posix()}'" for v in video_paths),
        encoding="utf-8",
    )
    await run_ffmpeg(
        [
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(output_path),
        ]
    )
    list_file.unlink(missing_ok=True)


def ffmpeg_available() -> bool:
    try:
        subprocess.run(
            [settings.ffmpeg_path, "-version"],
            check=True,
            capture_output=True,
        )
        return True
    except Exception:
        return False
