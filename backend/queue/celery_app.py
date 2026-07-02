from __future__ import annotations

from celery import Celery

from config import get_settings

settings = get_settings()

celery_app = Celery("drama", broker=settings.celery_broker_url, backend=settings.celery_result_backend)

celery_app.conf.task_routes = {
    "queue.tasks.parse_story": {"queue": "story"},
    "queue.tasks.generate_prompts": {"queue": "prompt"},
    "queue.tasks.generate_character": {"queue": "character"},
    "queue.tasks.generate_video": {"queue": "video"},
    "queue.tasks.merge_videos": {"queue": "editor"},
}
