from celery import Celery

from src.config import settings

celery_app = Celery(
    "typelingo",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.infrastructure.queue.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-expired-guests-daily": {
            "task": "src.infrastructure.queue.tasks.cleanup_expired_guests_task",
            "schedule": 86400,  # every 24 hours
        },
    },
)
