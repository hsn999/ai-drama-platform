from __future__ import annotations

from agents.base import extract_json, ollama_generate

WRITER_SYSTEM = "You are a short drama writer. Output valid JSON only."

WRITER_PROMPT = """Split the story into scenes and extract character profiles.

Output JSON:
{{
  "scenes": [{{"scene": 1, "description": "...", "characters": ["..."], "emotion": "...", "conflict": "...", "pace": "slow"}}],
  "characters_profile": [{{"name": "...", "gender": "...", "age": "...", "appearance": "...", "personality": "...", "costume": "..."}}]
}}

Story:
{story}
"""


async def parse_story(story: str, *, ollama_model: str | None = None) -> dict:
    raw = await ollama_generate(WRITER_PROMPT.format(story=story), WRITER_SYSTEM, model=ollama_model)
    data = extract_json(raw)
    if isinstance(data, list):
        return {"scenes": data, "characters_profile": []}
    return data
