from __future__ import annotations

import json

from agents.base import _mock_llm_response, extract_json, ollama_generate
from agents.subject_context import mock_writer_payload

WRITER_SYSTEM = (
    "You are a short drama writer. Output valid JSON only, no markdown or explanation. "
    "Follow the story exactly — animals stay animals, do not replace with humans."
)

WRITER_PROMPT = """Split the story into scenes and extract character profiles.
Use the story's actual subjects (person, animal, object) — do not invent human characters if story is about an animal.

Output JSON:
{{
  "scenes": [{{"scene": 1, "description": "...", "characters": ["..."], "emotion": "...", "conflict": "...", "pace": "slow"}}],
  "characters_profile": [{{"name": "...", "gender": "...", "age": "...", "appearance": "...", "personality": "...", "costume": "..."}}]
}}

Story:
{story}
"""


def _writer_fallback(story: str) -> dict:
    return mock_writer_payload(story)


async def parse_story(story: str, *, ollama_model: str | None = None) -> dict:
    raw = await ollama_generate(WRITER_PROMPT.format(story=story), WRITER_SYSTEM, model=ollama_model)
    try:
        data = extract_json(raw)
    except json.JSONDecodeError:
        try:
            data = extract_json(_mock_llm_response(f"{WRITER_SYSTEM}\n\n{WRITER_PROMPT.format(story=story)}"))
        except json.JSONDecodeError:
            data = _writer_fallback(story)
    if isinstance(data, list):
        return {"scenes": data, "characters_profile": []}
    return data
