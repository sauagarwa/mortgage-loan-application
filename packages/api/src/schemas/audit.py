"""
Audit log Pydantic schemas.
"""

from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Single audit log entry."""

    id: str
    timestamp: datetime
    user_id: str | None = None
    user_email: str | None = None
    user_role: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated audit log list."""

    items: list[AuditLogResponse]
    total: int
