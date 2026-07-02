from __future__ import annotations

from agents.base import ollama_generate
from agents.subject_context import enforce_subject_in_prompt

DIRECTOR_SYSTEM = (
    "You are a film director. Output optimized English prompt only. "
    "Enhance camera and atmosphere but NEVER change the main subject or species."
)

DIRECTOR_TEMPLATE = """Optimize this AI video prompt with stronger camera language and atmosphere (max 120 words).
Keep the same main subject (animal stays animal, dog stays dog).

Story context: {story}
Prompt: {prompt}
"""


async def optimize_prompt(
    prompt: str,
    *,
    story_context: str = "",
    ollama_model: str | None = None,
) -> str:
    story = (story_context or "").strip()
    raw = await ollama_generate(
        DIRECTOR_TEMPLATE.format(prompt=prompt, story=story or "none"),
        DIRECTOR_SYSTEM,
        model=ollama_model,
    )
    optimized = raw.strip().strip('"')
    return enforce_subject_in_prompt(optimized, story or prompt)
