from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "pdf_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=False,
)

celery_app.conf.beat_schedule = {
    "purge-expired-jobs-every-5-minutes": {
        "task": "purge_expired_jobs_task",
        "schedule": 300.0,
    },
}