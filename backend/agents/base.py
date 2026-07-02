from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx

from config import get_settings
from agents.subject_context import (
    extract_scenes_description,
    extract_story_from_blob,
    mock_storyboard_shots,
    mock_writer_payload,
    story_subject_en,
)

settings = get_settings()


def strip_llm_artifacts(text: str) -> str:
    """Remove qwen3-style thinking blocks."""
    text = re.sub(r"<\s*think\s*>[\s\S]*?<\s*/\s*think\s*>", "", text, flags=re.IGNORECASE)
    return text.strip()


def extract_json(text: str) -> Any:
    text = strip_llm_artifacts(text.strip())
    text = re.sub(r"^[\s\S]*?(?=\{|\[)", "", text)
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch not in "{[":
            continue
        try:
            value, _ = decoder.raw_decode(text[idx:])
            return value
        except json.JSONDecodeError:
            continue

    raise json.JSONDecodeError("No valid JSON found in LLM output", text, 0)


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
            return strip_llm_artifacts(resp.json()["response"])
    except Exception as exc:
        return _mock_llm_response(full_prompt, exc)


def _mock_llm_response(prompt: str, exc: Optional[Exception] = None) -> str:
    pl = prompt.lower()

    # Writer agent — must run before generic "character"/"appearance" checks
    if "split the story into scenes" in pl or (
        "short drama writer" in pl and "characters_profile" in prompt
    ):
        story = extract_story_from_blob(prompt)
        return json.dumps(mock_writer_payload(story), ensure_ascii=False)
    if "music video" in pl or ("shot_index" in prompt and "lyric_text" in prompt):
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
    if "storyboard" in pl or (
        "shot_index" in prompt and "camera_motion" in prompt and "duration" in prompt
    ):
        story = extract_story_from_blob(prompt)
        scene_desc = extract_scenes_description(prompt)
        count_m = re.search(r"Create\s+(\d+)\s+storyboard", prompt, re.I)
        shot_count = int(count_m.group(1)) if count_m else 3
        return json.dumps(
            mock_storyboard_shots(story, scene_desc, shot_count),
            ensure_ascii=False,
        )
    if "concept artist" in pl or ("name:" in pl and "appearance:" in pl and "style:" in pl):
        name_m = re.search(r"Name:\s*(.+)", prompt)
        app_m = re.search(r"Appearance:\s*(.+)", prompt)
        name = name_m.group(1).strip() if name_m else ""
        appearance = app_m.group(1).split("Style:")[0].strip() if app_m else ""
        if not appearance:
            app_m2 = re.search(r'"appearance":\s*"([^"]+)"', prompt)
            appearance = app_m2.group(1) if app_m2 else ""
        if not name:
            name_m2 = re.search(r'"name":\s*"([^"]+)"', prompt)
            name = name_m2.group(1) if name_m2 else ""
        subject = appearance or name or "character"
        en_subject = story_subject_en(subject)
        return (
            f"cinematic studio photo of {en_subject}, centered subject, plain background, "
            "soft lighting, highly detailed, sharp focus, 8k"
        )
    if "optimize this ai video prompt" in pl:
        return prompt.split("\n")[-1].strip() + ", cinematic lighting, 35mm film"
    if "video prompt engineer" in pl or "generate cinematic ai video prompt" in pl:
        story = extract_story_from_blob(prompt)
        shot: dict = {}
        shot_m = re.search(r"Shot:\s*(\{[\s\S]*?\})\s*\n", prompt)
        if shot_m:
            try:
                shot = json.loads(shot_m.group(1))
            except json.JSONDecodeError:
                pass
        style_m = re.search(r"Style:\s*(\S+)", prompt)
        style = style_m.group(1) if style_m else "cinematic"
        from agents.subject_context import baseline_shot_prompt, enforce_subject_in_prompt

        return enforce_subject_in_prompt(baseline_shot_prompt(shot, story, style), story)
    if "characters_profile" in prompt and "scenes" in prompt:
        story = extract_story_from_blob(prompt)
        return json.dumps(mock_writer_payload(story), ensure_ascii=False)
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
