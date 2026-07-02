from __future__ import annotations

import json

from agents.base import _mock_llm_response, extract_json, ollama_generate
from agents.subject_context import mock_storyboard_shots

STORYBOARD_SYSTEM = (
    "You are a film director. Output valid JSON array only. "
    "Match story subjects exactly — dog stories show a dog running, not humans."
)

STORYBOARD_PROMPT = """Create {shot_count} storyboard shots for these scenes.

Story context: {story}
Each shot: shot_index, camera, camera_motion, duration(5), action, environment, lighting, emotion
Action must describe the story subject (e.g. dog running, not a person standing).

Scenes:
{scenes}

Output JSON array only, no markdown.
"""


def _fallback_shots(scenes: list, shot_count: int, story: str = "") -> list:
    desc = story.strip()
    if not desc and scenes:
        first = scenes[0] if isinstance(scenes[0], dict) else {}
        desc = first.get("description") or ""
    return mock_storyboard_shots(story or desc, desc, shot_count)


async def create_storyboard(
    scenes: list,
    shot_count: int = 3,
    *,
    story_context: str = "",
    ollama_model: str | None = None,
) -> list:
    shot_count = max(shot_count, 1)
    story = (story_context or "").strip()
    formatted_prompt = STORYBOARD_PROMPT.format(
        scenes=json.dumps(scenes, ensure_ascii=False),
        shot_count=shot_count,
        story=story or "see scenes",
    )
    raw = await ollama_generate(
        formatted_prompt,
        STORYBOARD_SYSTEM,
        model=ollama_model,
    )
    try:
        shots = extract_json(raw)
    except json.JSONDecodeError:
        shots = extract_json(
            _mock_llm_response(f"{STORYBOARD_SYSTEM}\n\n{formatted_prompt}")
        )
    if isinstance(shots, dict):
        shots = shots.get("shots", [])
    if not isinstance(shots, list):
        shots = []
    if not shots:
        shots = _fallback_shots(scenes, shot_count, story)
    return shots[:shot_count]
