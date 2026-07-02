from __future__ import annotations

"""Celery tasks �?V1.1+ 启用，MVP 使用 asyncio 后台任务."""

from queue.celery_app import celery_app


@celery_app.task(name="queue.tasks.parse_story")
def parse_story_task(story: str) -> dict:
    raise NotImplementedError("Use asyncio pipeline in MVP")
