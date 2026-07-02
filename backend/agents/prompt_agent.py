from __future__ import annotations

import json

from agents.base import _mock_llm_response, extract_json, ollama_generate
from agents.subject_context import (
    baseline_shot_prompt,
    enforce_subject_in_prompt,
    subject_in_prompt,
)

PROMPT_SYSTEM = (
    "You are an AI video prompt engineer. Output English prompt only. "
    "Follow the story subject exactly — if story is about an animal, show the animal, not humans. "
    "Include action and motion for running scenes."
)

PROMPT_TEMPLATE = """Generate cinematic AI video prompt (English) for this shot.

Story context (must match subject): {story}
Shot: {shot}
Style: {style}

Requirements: full body or action framing for animals; include motion if story mentions running.
"""


async def generate_shot_prompt(
    shot: dict,
    style: str = "cinematic",
    *,
    story_context: str = "",
    ollama_model: str | None = None,
) -> str:
    story = (story_context or "").strip()
    baseline = baseline_shot_prompt(shot, story, style)
    raw = await ollama_generate(
        PROMPT_TEMPLATE.format(
            shot=json.dumps(shot, ensure_ascii=False),
            style=style,
            story=story or "none",
        ),
        PROMPT_SYSTEM,
        model=ollama_model,
    )
    prompt = raw.strip().strip('"')
    if prompt.startswith(("{", "[")):
        prompt = baseline
    if story and not subject_in_prompt(prompt, story):
        prompt = baseline
    return enforce_subject_in_prompt(prompt, story)


async def generate_all_prompts(
    shots: list, style: str = "cinematic", *, story_context: str = ""
) -> list:
    prompts = []
    for shot in shots:
        prompts.append(await generate_shot_prompt(shot, style, story_context=story_context))
    return prompts
