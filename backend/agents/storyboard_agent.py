from __future__ import annotations

import json

from agents.base import extract_json, ollama_generate

STORYBOARD_SYSTEM = "You are a film director. Output valid JSON array only."

STORYBOARD_PROMPT = """Create {shot_count} storyboard shots for these scenes.

Each shot: shot_index, camera, camera_motion, duration(5), action, environment, lighting, emotion

Scenes:
{scenes}

Output JSON array.
"""


async def create_storyboard(scenes: list, shot_count: int = 3, *, ollama_model: str | None = None) -> list:
    raw = await ollama_generate(
        STORYBOARD_PROMPT.format(
            scenes=json.dumps(scenes, ensure_ascii=False),
            shot_count=shot_count,
        ),
        STORYBOARD_SYSTEM,
        model=ollama_model,
    )
    shots = extract_json(raw)
    if isinstance(shots, dict):
        shots = shots.get("shots", [])
    return shots[:shot_count]
