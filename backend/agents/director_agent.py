from __future__ import annotations

from agents.base import ollama_generate

DIRECTOR_SYSTEM = "You are a film director. Output optimized English prompt only."

DIRECTOR_TEMPLATE = """Optimize this AI video prompt with stronger camera language and atmosphere (max 120 words):

{prompt}
"""


async def optimize_prompt(prompt: str, *, ollama_model: str | None = None) -> str:
    raw = await ollama_generate(DIRECTOR_TEMPLATE.format(prompt=prompt), DIRECTOR_SYSTEM, model=ollama_model)
    return raw.strip().strip('"')
