"""
Celery application configuration.

Worker can be started with:
    cd packages/api
    uv run celery -A src.worker.celery_app worker --loglevel=info
"""

from celery import Celery

from ..core.config import settings

celery_app = Celery(
    "mortgage-ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.worker.tasks.document_processing",
        "src.worker.tasks.risk_assessment",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task settings
    task_track_started=True,
    task_time_limit=600,  # 10 minute hard limit
    task_soft_time_limit=540,  # 9 minute soft limit
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    # Retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Queues
    task_default_queue="default",
    task_routes={
        "src.worker.tasks.document_processing.*": {"queue": "documents"},
        "src.worker.tasks.risk_assessment.*": {"queue": "risk"},
    },
)
