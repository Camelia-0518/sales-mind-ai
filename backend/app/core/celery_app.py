"""Celery application configuration."""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "salesmind",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.ai_engine",
        "app.services.email_service",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks (add tasks when they are implemented)
# celery_app.conf.beat_schedule = {}

if __name__ == "__main__":
    celery_app.start()
