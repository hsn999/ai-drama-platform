from __future__ import annotations

import json
from typing import Any

from agents.base import extract_json, ollama_generate
from mv_styles import MvStylePreset, get_mv_style

MV_DIRECTOR_SYSTEM = (
    "You are a vertical lyric MV director for Douyin/TikTok. "
    "Output valid JSON only, no markdown."
)

MV_DIRECTOR_TEMPLATE = """Create a vertical lyric music video shot list (Douyin style).

Song duration: {duration_sec:.1f}s
Style: {style_name} — {style_desc}
User theme / mood: {theme}
Lyric lines (with optional timestamps):
{lyrics_block}

Sections already detected:
{sections_json}

Requirements:
- Target {target_shots} shots total
- Chorus: fast cuts ~{chorus_sec}s per shot, high energy visuals
- Verse: ~{verse_sec}s per shot
- Intro/outro: ~{intro_sec}s per shot
- Each shot must cover the timeline without gaps; last shot ends at {duration_sec:.1f}s
- visual_prompt in English, vivid, trendy, high saturation, NO text in image
- lyric_text: Chinese or original lyric line shown during this shot (can be empty for instrumental)

Return JSON:
{{
  "shots": [
    {{
      "shot_index": 1,
      "section_type": "intro|verse|chorus|bridge|outro",
      "start_sec": 0.0,
      "end_sec": 5.0,
      "lyric_text": "歌词",
      "visual_prompt": "English scene description",
      "emotion": "melancholic",
      "camera_motion": "slow zoom in"
    }}
  ]
}}
"""


def _fallback_shots(
    sections: list[dict[str, Any]],
    lyric_lines: list[dict[str, Any]],
    duration_sec: float,
    style: MvStylePreset,
    target_shots: int,
    theme: str,
) -> list[dict[str, Any]]:
    shots: list[dict[str, Any]] = []
    idx = 1
    theme_hint = theme or "emotional night city"

    def shot_len(sec_type: str) -> float:
        if sec_type == "chorus":
            return style.chorus_shot_sec
        if sec_type in ("intro", "outro"):
            return style.intro_shot_sec
        return style.verse_shot_sec

    for sec in sections:
        sec_type = sec.get("type", "verse")
        t = float(sec["start_sec"])
        end = float(sec["end_sec"])
        lyrics = sec.get("lyric_lines") or []
        li = 0
        while t < end - 0.05 and idx <= target_shots:
            dur = min(shot_len(sec_type), end - t)
            lyric = lyrics[li] if li < len(lyrics) else ""
            if li < len(lyrics):
                li += 1
            emotion = "intense" if sec_type == "chorus" else "calm"
            motion = "fast push in" if sec_type == "chorus" else "slow zoom in"
            shots.append(
                {
                    "shot_index": idx,
                    "section_type": sec_type,
                    "start_sec": round(t, 2),
                    "end_sec": round(t + dur, 2),
                    "lyric_text": lyric,
                    "visual_prompt": (
                        f"{theme_hint}, {emotion} mood, {sec_type} section, "
                        f"trendy douyin aesthetic, neon lights, cinematic portrait"
                    ),
                    "emotion": emotion,
                    "camera_motion": motion,
                }
            )
            t += dur
            idx += 1

    if not shots:
        slot = duration_sec / max(target_shots, 1)
        for i in range(target_shots):
            start = i * slot
            end = duration_sec if i == target_shots - 1 else (i + 1) * slot
            lyric = lyric_lines[i]["text"] if i < len(lyric_lines) else ""
            shots.append(
                {
                    "shot_index": i + 1,
                    "section_type": "verse",
                    "start_sec": round(start, 2),
                    "end_sec": round(end, 2),
                    "lyric_text": lyric,
                    "visual_prompt": f"{theme_hint}, emotional vertical music video still",
                    "emotion": "melancholic",
                    "camera_motion": "slow zoom in",
                }
            )

    shots[-1]["end_sec"] = round(duration_sec, 2)
    return shots


async def plan_mv_shots(
    *,
    duration_sec: float,
    sections: list[dict[str, Any]],
    lyric_lines: list[dict[str, Any]],
    theme: str,
    style_id: str = "mv_lyric_pop",
    target_shots: int = 16,
    ollama_model: str | None = None,
) -> list[dict[str, Any]]:
    style = get_mv_style(style_id)
    lyrics_block = "\n".join(
        f"[{ln['start_sec']:.1f}s] {ln['text']}" for ln in lyric_lines[:40]
    ) or "(no lyrics)"

    prompt = MV_DIRECTOR_TEMPLATE.format(
        duration_sec=duration_sec,
        style_name=style.name,
        style_desc=style.description,
        theme=theme or "根据歌词情绪自动匹配",
        lyrics_block=lyrics_block,
        sections_json=json.dumps(sections, ensure_ascii=False),
        target_shots=target_shots,
        chorus_sec=style.chorus_shot_sec,
        verse_sec=style.verse_shot_sec,
        intro_sec=style.intro_shot_sec,
    )

    try:
        raw = await ollama_generate(prompt, MV_DIRECTOR_SYSTEM, model=ollama_model)
        data = extract_json(raw)
        shots = data.get("shots") if isinstance(data, dict) else data
        if isinstance(shots, list) and shots:
            return shots
    except Exception:
        pass

    return _fallback_shots(sections, lyric_lines, duration_sec, style, target_shots, theme)


def finalize_shot_prompt(visual_prompt: str, style_id: str = "mv_lyric_pop") -> str:
    style = get_mv_style(style_id)
    return f"{style.prompt_prefix}{visual_prompt}{style.prompt_suffix}"
