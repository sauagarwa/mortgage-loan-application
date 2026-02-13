"""
Health check endpoints
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from ..schemas.health import HealthResponse
from ..services.storage import check_health as check_minio_health

try:
    from db import DatabaseService, get_db_service  # type: ignore[import-untyped]
except Exception:
    # DB package not available or untyped
    DatabaseService = None  # type: ignore[assignment]
    get_db_service = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Capture API service startup time
API_START_TIME = datetime.now(UTC)

router = APIRouter()


def _check_celery_health() -> HealthResponse:
    """Check Celery worker health via Redis broker ping."""
    try:
        from ..worker.celery_app import celery_app

        inspector = celery_app.control.inspect(timeout=2.0)
        active = inspector.active()
        if active is not None:
            worker_count = len(active)
            return HealthResponse(
                name="Celery Workers",
                status="healthy",
                message=f"{worker_count} worker(s) connected",
                version="celery",
            )
        else:
            return HealthResponse(
                name="Celery Workers",
                status="degraded",
                message="No workers responding",
                version="celery",
            )
    except Exception as e:
        logger.warning(f"Celery health check failed: {e}")
        return HealthResponse(
            name="Celery Workers",
            status="unhealthy",
            message=f"Cannot reach workers: {str(e)[:100]}",
            version="celery",
        )


@router.get("/", response_model=list[HealthResponse])
async def health_check(
    db_service: DatabaseService | None = Depends(get_db_service) if get_db_service else None
) -> list[HealthResponse]:
    """Health check endpoint with dependency injection"""
    api_response = HealthResponse(
        name="API",
        status="healthy",
        message="API is running",
        version="0.1.0",
        start_time=API_START_TIME.isoformat()
    )

    # Get database health using dependency injection
    responses = [api_response]
    if db_service:
        db_health = await db_service.health_check()
        db_response = HealthResponse(**db_health)
        responses.append(db_response)

    # MinIO health
    minio_health = await check_minio_health()
    responses.append(
        HealthResponse(
            name="MinIO Storage",
            status=minio_health.get("status", "unknown"),
            message=f"Bucket: {minio_health.get('bucket', 'N/A')}",
            version="minio",
        )
    )

    # Celery worker health
    responses.append(_check_celery_health())

    return responses
