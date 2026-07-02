from __future__ import annotations

from typing import Iterable


def _fmt_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt_from_shots(shots: Iterable[dict]) -> str:
    blocks = []
    for shot in shots:
        start = float(shot["start_sec"])
        end = float(shot["end_sec"])
        text = (shot.get("lyric_text") or "").strip()
        if not text:
            continue
        blocks.append(f"{len(blocks) + 1}\n{_fmt_ts(start)} --> {_fmt_ts(end)}\n{text}\n")
    return "\n".join(blocks)


def build_ass_from_shots(
    shots: Iterable[dict],
    *,
    width: int = 1080,
    height: int = 1920,
    font_size: int = 72,
) -> str:
    """???????????????."""
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Lyric,Arial,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,40,40,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for shot in shots:
        text = (shot.get("lyric_text") or "").strip()
        if not text:
            continue
        start = _ass_ts(float(shot["start_sec"]))
        end = _ass_ts(float(shot["end_sec"]))
        safe = text.replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{start},{end},Lyric,,0,0,0,,{safe}\n")
    return "".join(lines)


def _ass_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"
