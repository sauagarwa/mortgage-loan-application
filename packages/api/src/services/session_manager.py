"""
Anonymous session management with Redis storage.

Provides session tokens for unauthenticated chat users, with linking
to Keycloak users when they authenticate.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass

import redis

from ..core.config import settings

logger = logging.getLogger(__name__)

SESSION_TTL = 86400  # 24 hours
SESSION_PREFIX = "chat:session:"


@dataclass
class SessionData:
    """Data stored for a chat session."""

    session_id: str
    conversation_id: str | None = None
    user_id: str | None = None
    application_id: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "SessionData":
        return cls(**json.loads(data))


def _get_redis() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def create_session() -> SessionData:
    """Create a new anonymous session."""
    session_id = str(uuid.uuid4())
    session = SessionData(session_id=session_id)
    r = _get_redis()
    r.setex(f"{SESSION_PREFIX}{session_id}", SESSION_TTL, session.to_json())
    r.close()
    logger.info(f"Created chat session: {session_id}")
    return session


def get_session(session_id: str) -> SessionData | None:
    """Retrieve session data by ID."""
    r = _get_redis()
    data = r.get(f"{SESSION_PREFIX}{session_id}")
    r.close()
    if data is None:
        return None
    return SessionData.from_json(data)


def update_session(session: SessionData) -> None:
    """Update session data in Redis."""
    r = _get_redis()
    r.setex(f"{SESSION_PREFIX}{session.session_id}", SESSION_TTL, session.to_json())
    r.close()


def link_session_to_user(session_id: str, user_id: str) -> SessionData | None:
    """Link an anonymous session to an authenticated user."""
    session = get_session(session_id)
    if session is None:
        return None
    session.user_id = user_id
    update_session(session)
    logger.info(f"Linked session {session_id} to user {user_id}")
    return session
