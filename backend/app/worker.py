"""
Celery worker configuration for background tasks
"""

from celery import Celery
from celery.schedules import crontab
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Create Celery app
celery_app = Celery(
    "ai_blog_assistant",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.content_generation",
        "app.tasks.publishing",
        "app.tasks.analytics",
        "app.tasks.comment_analysis",
        "app.tasks.folder_monitoring",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Check for new folders every minute
    "check-folders": {
        "task": "app.tasks.folder_monitoring.check_new_folders",
        "schedule": 60.0,  # Every minute
    },
    
    # Collect analytics data every hour
    "collect-analytics": {
        "task": "app.tasks.analytics.collect_platform_analytics",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Analyze comments every 6 hours
    "analyze-comments": {
        "task": "app.tasks.comment_analysis.analyze_new_comments",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    
    # Generate content recommendations daily
    "generate-recommendations": {
        "task": "app.tasks.analytics.generate_content_recommendations",
        "schedule": crontab(minute=0, hour=9),  # Daily at 9 AM
    },
    
    # Cleanup old logs and temporary files weekly
    "cleanup-files": {
        "task": "app.tasks.maintenance.cleanup_old_files",
        "schedule": crontab(minute=0, hour=2, day_of_week=0),  # Weekly on Sunday at 2 AM
    },
}

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    logger.info("Debug task executed", task_id=self.request.id)
    return f"Request: {self.request!r}"

if __name__ == "__main__":
    celery_app.start()