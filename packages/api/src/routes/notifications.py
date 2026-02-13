"""
Notification routes - list, read, and manage notifications.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import Notification, User, get_db

from ..core.security import TokenUser, get_current_user
from ..schemas.notifications import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)

router = APIRouter()


async def _get_db_user(user: TokenUser, session: AsyncSession) -> User:
    """Get the local user record for the authenticated user."""
    result = await session.execute(
        select(User).where(User.keycloak_id == user.keycloak_id)
    )
    db_user = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User record not found",
        )
    return db_user


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    """List notifications for the current user."""
    db_user = await _get_db_user(user, session)

    query = select(Notification).where(Notification.user_id == db_user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Unread count (always)
    unread_result = await session.execute(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == db_user.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    unread_count = unread_result.scalar() or 0

    # Fetch paginated results
    query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    notifications = result.scalars().all()

    return NotificationListResponse(
        items=[
            NotificationResponse(
                id=str(n.id),
                type=n.type,
                title=n.title,
                message=n.message,
                application_id=str(n.application_id) if n.application_id else None,
                is_read=n.is_read,
                created_at=n.created_at,
            )
            for n in notifications
        ],
        total=total,
        unread_count=unread_count,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UnreadCountResponse:
    """Get the count of unread notifications."""
    db_user = await _get_db_user(user, session)

    result = await session.execute(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == db_user.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    count = result.scalar() or 0

    return UnreadCountResponse(unread_count=count)


@router.put("/{notification_id}/read", status_code=204)
async def mark_notification_read(
    notification_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Mark a single notification as read."""
    db_user = await _get_db_user(user, session)

    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == db_user.id,
        )
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    await session.commit()


@router.post("/mark-all-read", status_code=204)
async def mark_all_read(
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Mark all notifications as read for the current user."""
    db_user = await _get_db_user(user, session)

    await session.execute(
        update(Notification)
        .where(
            Notification.user_id == db_user.id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    await session.commit()


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a notification."""
    db_user = await _get_db_user(user, session)

    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == db_user.id,
        )
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    await session.delete(notification)
    await session.commit()
