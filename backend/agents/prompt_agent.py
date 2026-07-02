from __future__ import annotations

import json

from agents.base import ollama_generate

PROMPT_SYSTEM = "You are an AI video prompt engineer. Output English prompt only."

PROMPT_TEMPLATE = """Generate cinematic AI video prompt (English) for this shot:

{shot}

Style: {style}
"""


async def generate_shot_prompt(shot: dict, style: str = "cinematic", *, ollama_model: str | None = None) -> str:
    raw = await ollama_generate(
        PROMPT_TEMPLATE.format(
            shot=json.dumps(shot, ensure_ascii=False),
            style=style,
        ),
        PROMPT_SYSTEM,
        model=ollama_model,
    )
    return raw.strip().strip('"')


async def generate_all_prompts(shots: list, style: str = "cinematic") -> list:
    prompts = []
    for shot in shots:
        prompts.append(await generate_shot_prompt(shot, style))
    return prompts
