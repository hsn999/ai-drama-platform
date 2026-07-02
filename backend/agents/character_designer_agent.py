from __future__ import annotations

from agents.base import ollama_generate
from agents.subject_context import subject_in_prompt, story_subject_en

CHARACTER_DESIGNER_SYSTEM = (
    "You are a character concept artist. Output English image prompt only. "
    "Follow the profile exactly — subject may be human, animal, creature, or object. "
    "Never change species or category (e.g. dog stays dog, not person)."
)

CHARACTER_DESIGNER_PROMPT = """Generate an AI image prompt (English) for the subject below.

Requirements:
- Match the profile species/type exactly (animal stays animal)
- Centered subject, clear view, plain background, cinematic, max 100 words
- Bust/headshot for humans; full body or portrait framing for animals/objects

Name: {name}
Appearance: {appearance}
Style: {style}
"""


async def design_character_prompt(profile: dict, style: str = "cinematic", *, ollama_model: str | None = None) -> str:
    name = (profile.get("name") or "").strip()
    appearance = (profile.get("appearance") or profile.get("description") or "").strip()
    raw = await ollama_generate(
        CHARACTER_DESIGNER_PROMPT.format(
            name=name,
            appearance=appearance,
            style=style,
        ),
        CHARACTER_DESIGNER_SYSTEM,
        model=ollama_model,
    )
    prompt = raw.strip().strip('"')
    # 确保用户描述（如「小狗」）不被 LLM 丢掉；Flux 对英文更稳
    if appearance and not subject_in_prompt(prompt, appearance):
        prefix = story_subject_en(appearance)
        prompt = f"{prefix}, {name}, {prompt}" if name else f"{prefix}, {prompt}"
    return prompt

