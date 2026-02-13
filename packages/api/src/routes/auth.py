"""
Authentication routes - Keycloak config and user profile management.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import User, get_db

from ..core.config import settings
from ..core.security import TokenUser, get_current_user
from ..schemas.auth import KeycloakConfigResponse, UserProfileResponse, UserProfileUpdate

router = APIRouter()


@router.get("/config", response_model=KeycloakConfigResponse)
async def get_keycloak_config() -> KeycloakConfigResponse:
    """Return Keycloak realm configuration for frontend initialization.

    This endpoint is unauthenticated so the frontend can initialize Keycloak.
    """
    return KeycloakConfigResponse(
        realm=settings.KEYCLOAK_REALM,
        auth_server_url=settings.KEYCLOAK_SERVER_URL,
        client_id=settings.KEYCLOAK_CLIENT_ID_UI,
        ssl_required="external",
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Get the authenticated user's profile.

    Creates or updates the local user record from Keycloak token data.
    """
    # Find or create local user record
    result = await session.execute(
        select(User).where(User.keycloak_id == user.keycloak_id)
    )
    db_user = result.scalar_one_or_none()

    if db_user is None:
        db_user = User(
            keycloak_id=user.keycloak_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.primary_role,
            last_login_at=datetime.now(UTC),
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
    else:
        # Update last login and sync Keycloak data
        db_user.last_login_at = datetime.now(UTC)
        db_user.email = user.email
        db_user.first_name = user.first_name
        db_user.last_name = user.last_name
        db_user.role = user.primary_role
        await session.commit()
        await session.refresh(db_user)

    return UserProfileResponse(
        id=str(db_user.id),
        email=db_user.email,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        phone=db_user.phone,
        role=db_user.role,
        roles=user.roles,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None,
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update the authenticated user's profile."""
    result = await session.execute(
        select(User).where(User.keycloak_id == user.keycloak_id)
    )
    db_user = result.scalar_one_or_none()

    if db_user is None:
        # Create if doesn't exist
        db_user = User(
            keycloak_id=user.keycloak_id,
            email=user.email,
            first_name=profile_data.first_name or user.first_name,
            last_name=profile_data.last_name or user.last_name,
            phone=profile_data.phone,
            role=user.primary_role,
        )
        session.add(db_user)
    else:
        if profile_data.first_name is not None:
            db_user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            db_user.last_name = profile_data.last_name
        if profile_data.phone is not None:
            db_user.phone = profile_data.phone

    await session.commit()
    await session.refresh(db_user)

    return UserProfileResponse(
        id=str(db_user.id),
        email=db_user.email,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        phone=db_user.phone,
        role=db_user.role,
        roles=user.roles,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None,
    )
