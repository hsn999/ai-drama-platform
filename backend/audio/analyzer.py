from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from config import get_settings

settings = get_settings()

_LRC_LINE = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\](.*)")


def probe_audio_duration(audio_path: Path) -> float:
    cmd = [
        settings.ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(audio_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    return float(data["format"]["duration"])


def parse_lrc(lrc_text: str) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for raw in lrc_text.splitlines():
        m = _LRC_LINE.match(raw.strip())
        if not m:
            continue
        mm, ss, frac, text = m.groups()
        sec = int(mm) * 60 + int(ss)
        if frac:
            sec += int(frac.ljust(3, "0")[:3]) / 1000.0
        text = text.strip()
        if text:
            lines.append({"start_sec": sec, "text": text})
    lines.sort(key=lambda x: x["start_sec"])
    for i, line in enumerate(lines):
        if i + 1 < len(lines):
            line["end_sec"] = lines[i + 1]["start_sec"]
        else:
            line["end_sec"] = None
    return lines


def distribute_lyric_lines(lyrics_text: str, duration_sec: float) -> list[dict[str, Any]]:
    lines = [ln.strip() for ln in lyrics_text.splitlines() if ln.strip()]
    if not lines:
        return []
    if len(lines) == 1:
        return [{"start_sec": 0.0, "end_sec": duration_sec, "text": lines[0]}]
    slot = duration_sec / len(lines)
    result = []
    for i, text in enumerate(lines):
        start = i * slot
        end = duration_sec if i == len(lines) - 1 else (i + 1) * slot
        result.append({"start_sec": start, "end_sec": end, "text": text})
    return result


def build_sections_from_lyrics(
    lyric_lines: list[dict[str, Any]],
    duration_sec: float,
) -> list[dict[str, Any]]:
    """按歌词行数粗分 intro / verse / chorus 段落（无 LLM 时的兜底）."""
    if not lyric_lines:
        return [
            {
                "type": "verse",
                "start_sec": 0.0,
                "end_sec": duration_sec,
                "energy": 0.5,
                "lyric_lines": [],
            }
        ]

    n = len(lyric_lines)
    third = max(n // 3, 1)
    chunks = [
        ("intro", lyric_lines[: max(1, third // 2)]),
        ("verse", lyric_lines[max(1, third // 2) : third]),
        ("chorus", lyric_lines[third : 2 * third]),
        ("verse", lyric_lines[2 * third :]),
    ]
    sections = []
    for sec_type, lines in chunks:
        if not lines:
            continue
        start = lines[0]["start_sec"]
        end = lines[-1].get("end_sec") or duration_sec
        energy = 0.9 if sec_type == "chorus" else 0.4 if sec_type == "intro" else 0.6
        sections.append(
            {
                "type": sec_type,
                "start_sec": start,
                "end_sec": end,
                "energy": energy,
                "lyric_lines": [ln["text"] for ln in lines],
            }
        )
    if sections:
        sections[-1]["end_sec"] = duration_sec
    return sections
