"""
Audit log routes — admin-only access to view audit trail.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import AuditLog, get_db

from ..core.security import TokenUser, get_current_user, require_role
from ..schemas.audit import AuditLogListResponse, AuditLogResponse

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
@require_role(["admin", "loan_servicer"])
async def list_audit_logs(
    action: str | None = Query(None, description="Filter by action"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: UUID | None = Query(None, description="Filter by resource ID"),
    user_email: str | None = Query(None, description="Filter by user email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AuditLogListResponse:
    """List audit log entries with optional filters."""
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)
    if user_email:
        query = query.where(AuditLog.user_email.ilike(f"%{user_email}%"))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    logs = result.scalars().all()

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=str(log.id),
                timestamp=log.timestamp,
                user_id=str(log.user_id) if log.user_id else None,
                user_email=log.user_email,
                user_role=log.user_role,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                details=log.details,
                ip_address=str(log.ip_address) if log.ip_address else None,
                user_agent=log.user_agent,
            )
            for log in logs
        ],
        total=total,
    )
