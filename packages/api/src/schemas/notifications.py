"""
Notification Pydantic schemas.
"""

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Single notification response."""

    id: str
    type: str
    title: str
    message: str
    application_id: str | None = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Paginated notification list."""

    items: list[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Unread notification count."""

    unread_count: int
