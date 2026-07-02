from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx

from config import get_settings

settings = get_settings()


def extract_json(text: str) -> Any:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    return json.loads(text)


async def ollama_generate(prompt: str, system: Optional[str] = None, model: Optional[str] = None) -> str:
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    model_name = model or settings.ollama_model
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": full_prompt,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["response"]
    except Exception as exc:
        return _mock_llm_response(full_prompt, exc)


def _mock_llm_response(prompt: str, exc: Optional[Exception] = None) -> str:
    if "music video" in prompt.lower() or "shot_index" in prompt and "lyric_text" in prompt:
        return json.dumps(
            {
                "shots": [
                    {
                        "shot_index": 1,
                        "section_type": "intro",
                        "start_sec": 0.0,
                        "end_sec": 5.0,
                        "lyric_text": "夜色慢慢落下",
                        "visual_prompt": "lonely city rooftop at night, neon lights, rain reflections",
                        "emotion": "melancholic",
                        "camera_motion": "slow zoom in",
                    },
                    {
                        "shot_index": 2,
                        "section_type": "verse",
                        "start_sec": 5.0,
                        "end_sec": 12.0,
                        "lyric_text": "回忆在耳边说话",
                        "visual_prompt": "close-up portrait in neon alley, vibrant colors, emotional",
                        "emotion": "nostalgic",
                        "camera_motion": "slow pan",
                    },
                    {
                        "shot_index": 3,
                        "section_type": "chorus",
                        "start_sec": 12.0,
                        "end_sec": 15.5,
                        "lyric_text": "让我们一起唱",
                        "visual_prompt": "dynamic concert lights, crowd bokeh, high energy",
                        "emotion": "euphoric",
                        "camera_motion": "fast push in",
                    },
                ]
            },
            ensure_ascii=False,
        )
    if "storyboard" in prompt.lower() or "shot_index" in prompt:
        return json.dumps(
            [
                {
                    "shot_index": 1,
                    "camera": "wide",
                    "camera_motion": "slow push-in",
                    "duration": 5,
                    "action": "hero walks into rainy inn",
                    "environment": "rainy night inn",
                    "lighting": "moody backlit",
                    "emotion": "tension",
                },
                {
                    "shot_index": 2,
                    "camera": "close-up",
                    "camera_motion": "static",
                    "duration": 5,
                    "action": "hero looks up with sharp eyes",
                    "environment": "inn hall",
                    "lighting": "candlelit",
                    "emotion": "anger",
                },
                {
                    "shot_index": 3,
                    "camera": "medium",
                    "camera_motion": "tracking",
                    "duration": 5,
                    "action": "draws sword, blade flashes",
                    "environment": "inn courtyard",
                    "lighting": "rain night",
                    "emotion": "climax",
                },
            ],
            ensure_ascii=False,
        )
    if "character" in prompt.lower() and "prompt" in prompt.lower():
        return (
            "cinematic portrait of a young swordsman, black robe, sharp eyes, "
            "plain background, studio lighting, highly detailed, movie still"
        )
    if "optimize" in prompt.lower() or "director" in prompt.lower():
        return prompt.split("\n")[-1].strip() + ", cinematic lighting, 35mm film"
    if "characters_profile" in prompt or "scenes" in prompt:
        return json.dumps(
            {
                "scenes": [
                    {
                        "scene": 1,
                        "description": "rainy night inn",
                        "characters": ["hero"],
                        "emotion": "tense",
                        "conflict": "enemy appears",
                        "pace": "slow",
                    }
                ],
                "characters_profile": [
                    {
                        "name": "hero",
                        "gender": "male",
                        "age": "25",
                        "appearance": "sharp eyes, black robe",
                        "personality": "calm",
                        "costume": "black wuxia robe",
                    }
                ],
            },
            ensure_ascii=False,
        )
    return json.dumps(
        [
            {
                "scene": 1,
                "description": "rainy night inn",
                "characters": ["hero"],
                "emotion": "tense",
                "conflict": "enemy appears",
                "pace": "slow",
            }
        ],
        ensure_ascii=False,
    )
