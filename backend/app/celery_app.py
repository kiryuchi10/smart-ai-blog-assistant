"""
Celery application configuration for background tasks
"""
from celery import Celery
from .core.config import settings

# Create Celery instance
celery_app = Celery(
    "ai_blog_assistant",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    "process-scheduled-posts": {
        "task": "app.tasks.process_scheduled_posts",
        "schedule": 60.0,  # Run every minute
    },
    "cleanup-expired-tokens": {
        "task": "app.tasks.cleanup_expired_tokens",
        "schedule": 3600.0,  # Run every hour
    },
}