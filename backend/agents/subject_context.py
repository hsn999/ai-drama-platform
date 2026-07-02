from __future__ import annotations

import json
import re
from typing import Any

SUBJECT_CN_EN: dict[str, str] = {
    "小狗": "cute puppy dog",
    "大狗": "large dog",
    "狗": "dog",
    "小猫": "kitten cat",
    "猫": "cat",
    "兔子": "rabbit",
    "鸟": "bird",
}

MOTION_CN_EN: dict[str, str] = {
    "奔跑": "running fast",
    "跑": "running",
    "跳": "jumping",
    "飞": "flying",
}

ANIMAL_KEYWORDS = ("狗", "猫", "兔", "鸟", "dog", "cat", "puppy", "kitten", "rabbit", "bird")
HUMAN_KEYWORDS = ("人", "男", "女", "少年", "女孩", "man", "woman", "person", "human", "boy", "girl")


def is_animal_story(text: str) -> bool:
    t = text.lower()
    return any(k in text or k in t for k in ANIMAL_KEYWORDS) and not any(
        k in text or k in t for k in HUMAN_KEYWORDS
    )


def is_running_story(text: str) -> bool:
    t = text.lower()
    return "跑" in text or "running" in t or "run" in t


def story_subject_en(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "cinematic scene"
    subject = text[:120]
    for cn, en in SUBJECT_CN_EN.items():
        if cn in text:
            subject = en
            break
    for cn, en in MOTION_CN_EN.items():
        if cn in text:
            subject = f"{subject} {en}"
            break
    return subject


def subject_in_prompt(prompt: str, story: str) -> bool:
    if not story.strip():
        return True
    prompt_l = prompt.lower()
    for cn, en in SUBJECT_CN_EN.items():
        if cn in story and (en.split()[0] in prompt_l or en in prompt_l):
            return True
    for token in story.replace("，", " ").replace(",", " ").split():
        t = token.strip()
        if len(t) >= 2 and t.lower() in prompt_l:
            return True
    if is_running_story(story) and ("running" in prompt_l or "run" in prompt_l):
        return True
    return False


def enforce_subject_in_prompt(prompt: str, story: str) -> str:
    prompt = prompt.strip()
    if not story.strip():
        return prompt
    if subject_in_prompt(prompt, story):
        if is_running_story(story) and "running" not in prompt.lower():
            return f"{story_subject_en(story)}, dynamic action, motion blur, {prompt}"
        return prompt
    prefix = story_subject_en(story)
    guards = ", no humans, no people, animal only" if is_animal_story(story) else ""
    motion = ", dynamic action shot, motion blur" if is_running_story(story) else ""
    return f"{prefix}{motion}{guards}, {prompt}"


def extract_story_from_blob(text: str) -> str:
    for pattern in (
        r"Story:\s*\n([\s\S]+?)(?:\n\n|\Z)",
        r"Story context:\s*(.+)",
    ):
        m = re.search(pattern, text)
        if m:
            val = m.group(1).strip()
            if val and val.lower() not in ("none", "see scenes"):
                return val
    return ""


def extract_scenes_description(text: str) -> str:
    m = re.search(r"Scenes:\s*\n(\[[\s\S]*?\])", text)
    if not m:
        return ""
    try:
        scenes = json.loads(m.group(1))
        if scenes and isinstance(scenes[0], dict):
            return str(scenes[0].get("description") or "")
    except json.JSONDecodeError:
        pass
    return ""


def mock_writer_payload(story: str) -> dict[str, Any]:
    excerpt = (story or "opening scene").strip()[:300]
    subject = story_subject_en(excerpt)
    char_name = "小狗" if "狗" in excerpt else "主角"
    return {
        "scenes": [
            {
                "scene": 1,
                "description": excerpt,
                "characters": [char_name],
                "emotion": "energetic" if is_running_story(excerpt) else "neutral",
                "conflict": "story begins",
                "pace": "fast" if is_running_story(excerpt) else "medium",
            }
        ],
        "characters_profile": [
            {
                "name": char_name,
                "gender": "unknown",
                "age": "young",
                "appearance": subject,
                "personality": "playful",
                "costume": "natural fur",
            }
        ],
    }


def mock_storyboard_shots(story: str, scene_desc: str, shot_count: int) -> list[dict[str, Any]]:
    context = scene_desc or story
    subject = story_subject_en(context)
    running = is_running_story(context)
    verb = "running forward on a path" if running else "in scene"
    templates = [
        {
            "camera": "wide",
            "camera_motion": "tracking",
            "action": f"wide tracking shot, {subject} {verb}, outdoor environment",
            "environment": context,
            "lighting": "natural daylight",
            "emotion": "joyful" if running else "calm",
        },
        {
            "camera": "medium",
            "camera_motion": "slow push-in",
            "action": f"medium action shot, {subject} {verb}, side view, motion blur",
            "environment": context,
            "lighting": "cinematic contrast",
            "emotion": "focused",
        },
        {
            "camera": "low",
            "camera_motion": "tracking",
            "action": f"low angle dynamic shot, {subject} {verb}, grass and ground visible",
            "environment": context,
            "lighting": "warm sunlight",
            "emotion": "energetic",
        },
    ]
    shots = []
    for i in range(max(shot_count, 1)):
        item = dict(templates[i % len(templates)])
        item["shot_index"] = i + 1
        item["duration"] = 5
        shots.append(item)
    return shots


def motion_from_camera(camera_motion: str | None) -> str:
    if not camera_motion:
        return "zoom_in"
    cm = camera_motion.lower()
    if "pull" in cm or "zoom out" in cm or "out" in cm:
        return "zoom_out"
    if "pan_left" in cm or "left" in cm:
        return "pan_left"
    if "pan_right" in cm or "right" in cm:
        return "pan_right"
    if "track" in cm:
        return "zoom_in"
    return "zoom_in"


def baseline_shot_prompt(shot: dict, story: str, style: str) -> str:
    action = shot.get("action") or ""
    env = shot.get("environment") or ""
    subject = story_subject_en(story)
    guards = ", no humans, animal only" if is_animal_story(story) else ""
    motion = ", dynamic action, motion blur" if is_running_story(story) else ""
    return f"{subject}{motion}, {action}, {env}, {style} cinematic{guards}".strip(", ")
