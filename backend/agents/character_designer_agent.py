from __future__ import annotations

import json

from agents.base import ollama_generate

CHARACTER_DESIGNER_SYSTEM = "You are a character concept artist. Output English prompt only."

CHARACTER_DESIGNER_PROMPT = """Generate an AI image prompt (English) for a character portrait.

Requirements: bust or headshot, front or 3/4 view, plain background, cinematic, max 100 words.

Profile:
{profile}

Style: {style}
"""


async def design_character_prompt(profile: dict, style: str = "cinematic", *, ollama_model: str | None = None) -> str:
    raw = await ollama_generate(
        CHARACTER_DESIGNER_PROMPT.format(
            profile=json.dumps(profile, ensure_ascii=False),
            style=style,
        ),
        CHARACTER_DESIGNER_SYSTEM,
        model=ollama_model,
    )
    return raw.strip().strip('"')
