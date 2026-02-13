"""
Audit logging service — helpers to create audit log entries.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db import AuditLog


async def create_audit_log(
    session: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: UUID | str | None = None,
    user_id: UUID | str | None = None,
    user_email: str | None = None,
    user_role: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Create an audit log entry."""
    if isinstance(resource_id, str):
        resource_id = UUID(resource_id)
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    entry = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(entry)
    await session.flush()
    return entry
