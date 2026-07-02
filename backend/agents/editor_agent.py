from __future__ import annotations

"""Editor agent �?字幕与剪辑元数据（MVP 占位�?"""

from typing import Any


async def build_edit_plan(shots: list[dict], story: str) -> dict[str, Any]:
    return {
        "transitions": ["fade"] * max(len(shots) - 1, 0),
        "subtitles": [],
        "bgm": None,
    }
