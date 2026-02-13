"""
Synchronous database session for Celery workers.

Celery tasks run in synchronous context, so we need sync SQLAlchemy sessions
instead of the async ones used by FastAPI.
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings

# Create sync engine from the async URL
sync_url = settings.database_url_sync

sync_engine = create_engine(sync_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
SyncSessionLocal = sessionmaker(bind=sync_engine, class_=Session)


@contextmanager
def get_sync_session():
    """Context manager for synchronous database sessions in Celery tasks."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
