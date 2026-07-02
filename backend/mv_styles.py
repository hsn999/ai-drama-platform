"""MV 视觉风格预设 — 竖屏歌词 MV（抖音风）为默认."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MvStylePreset:
    id: str
    name: str
    aspect_ratio: str
    output_resolution: str
    gen_resolution: str
    prompt_prefix: str
    prompt_suffix: str
    subtitle_style: str
    verse_shot_sec: float
    chorus_shot_sec: float
    intro_shot_sec: float
    description: str


MV_LYRIC_POP = MvStylePreset(
    id="mv_lyric_pop",
    name="竖屏歌词 MV（抖音风）",
    aspect_ratio="9:16",
    output_resolution="1080x1920",
    gen_resolution="768x1344",
    prompt_prefix=(
        "vertical 9:16 music video still, trendy douyin aesthetic, vibrant neon colors, "
        "high contrast, cinematic lighting, emotional, "
    ),
    prompt_suffix=(
        ", ultra sharp, no text, no watermark, no logo, portrait orientation"
    ),
    subtitle_style="bold_bottom",
    verse_shot_sec=7.0,
    chorus_shot_sec=3.5,
    intro_shot_sec=5.0,
    description="字幕突出、副歌快切、高饱和竖屏画面，适合 Suno 歌曲发抖音/视频号。",
)

PRESETS: dict[str, MvStylePreset] = {
    MV_LYRIC_POP.id: MV_LYRIC_POP,
}

DEFAULT_MV_STYLE = MV_LYRIC_POP.id


def get_mv_style(style_id: str | None = None) -> MvStylePreset:
    return PRESETS.get(style_id or DEFAULT_MV_STYLE, MV_LYRIC_POP)
