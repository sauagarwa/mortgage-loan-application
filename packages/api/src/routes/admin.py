"""
Admin routes — LLM provider config, user management, system health.
"""

import logging
import time
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import Application, LLMConfig, User, get_db

from ..core.config import settings
from ..core.security import TokenUser, get_current_user, require_role
from ..schemas.admin import (
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdate,
    ComponentHealth,
    LLMProviderCreate,
    LLMProviderResponse,
    LLMProviderUpdate,
    LLMTestResult,
    SystemHealthResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── LLM Provider Configuration ──────────────────────────────────────────

def _llm_to_response(config: LLMConfig) -> LLMProviderResponse:
    return LLMProviderResponse(
        id=str(config.id),
        provider=config.provider,
        is_active=config.is_active,
        is_default=config.is_default,
        base_url=config.base_url,
        api_key_set=bool(config.api_key_encrypted),
        default_model=config.default_model,
        max_tokens=config.max_tokens,
        temperature=float(config.temperature),
        rate_limit_rpm=config.rate_limit_rpm,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/llm-config", response_model=list[LLMProviderResponse])
@require_role(["admin"])
async def list_llm_configs(
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[LLMProviderResponse]:
    """List all LLM provider configurations."""
    result = await session.execute(select(LLMConfig).order_by(LLMConfig.provider))
    configs = result.scalars().all()
    return [_llm_to_response(c) for c in configs]


@router.post("/llm-config", response_model=LLMProviderResponse, status_code=201)
@require_role(["admin"])
async def create_llm_config(
    data: LLMProviderCreate,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LLMProviderResponse:
    """Create a new LLM provider configuration."""
    existing = await session.execute(
        select(LLMConfig).where(LLMConfig.provider == data.provider)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider '{data.provider}' already exists",
        )

    if data.is_default:
        await session.execute(
            update(LLMConfig).values(is_default=False)
        )

    config = LLMConfig(
        provider=data.provider,
        base_url=data.base_url,
        api_key_encrypted=data.api_key,
        default_model=data.default_model,
        max_tokens=data.max_tokens,
        temperature=data.temperature,
        rate_limit_rpm=data.rate_limit_rpm,
        is_active=data.is_active,
        is_default=data.is_default,
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return _llm_to_response(config)


@router.put("/llm-config/{provider}", response_model=LLMProviderResponse)
@require_role(["admin"])
async def update_llm_config(
    provider: str,
    data: LLMProviderUpdate,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LLMProviderResponse:
    """Update an LLM provider configuration."""
    result = await session.execute(
        select(LLMConfig).where(LLMConfig.provider == provider)
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not found",
        )

    if data.is_default and not config.is_default:
        await session.execute(
            update(LLMConfig).where(LLMConfig.id != config.id).values(is_default=False)
        )

    if data.is_active is not None:
        config.is_active = data.is_active
    if data.is_default is not None:
        config.is_default = data.is_default
    if data.base_url is not None:
        config.base_url = data.base_url
    if data.api_key is not None:
        config.api_key_encrypted = data.api_key
    if data.default_model is not None:
        config.default_model = data.default_model
    if data.max_tokens is not None:
        config.max_tokens = data.max_tokens
    if data.temperature is not None:
        config.temperature = data.temperature
    if data.rate_limit_rpm is not None:
        config.rate_limit_rpm = data.rate_limit_rpm

    await session.commit()
    await session.refresh(config)
    return _llm_to_response(config)


@router.post("/llm-config/{provider}/test", response_model=LLMTestResult)
@require_role(["admin"])
async def test_llm_config(
    provider: str,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LLMTestResult:
    """Test an LLM provider connection."""
    result = await session.execute(
        select(LLMConfig).where(LLMConfig.provider == provider)
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not found",
        )

    try:
        import httpx

        start = time.time()
        headers = {"Content-Type": "application/json"}
        if config.api_key_encrypted:
            headers["Authorization"] = f"Bearer {config.api_key_encrypted}"

        if provider == "anthropic":
            headers["x-api-key"] = config.api_key_encrypted or ""
            headers["anthropic-version"] = "2023-06-01"
            test_url = f"{config.base_url}/messages"
            payload = {
                "model": config.default_model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "ping"}],
            }
        else:
            test_url = f"{config.base_url}/chat/completions"
            payload = {
                "model": config.default_model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "ping"}],
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(test_url, headers=headers, json=payload)

        latency = (time.time() - start) * 1000

        if response.status_code < 500:
            return LLMTestResult(
                provider=provider,
                success=True,
                message=f"Connection successful (HTTP {response.status_code})",
                latency_ms=round(latency, 1),
            )
        else:
            return LLMTestResult(
                provider=provider,
                success=False,
                message=f"Server error: HTTP {response.status_code}",
                latency_ms=round(latency, 1),
            )

    except Exception as e:
        return LLMTestResult(
            provider=provider,
            success=False,
            message=f"Connection failed: {str(e)[:200]}",
        )


# ── User Management ─────────────────────────────────────────────────────

@router.get("/users", response_model=AdminUserListResponse)
@require_role(["admin"])
async def list_users(
    search: str | None = Query(None, description="Search by email or name"),
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdminUserListResponse:
    """List users with optional filters."""
    query = select(User)

    if search:
        like = f"%{search}%"
        query = query.where(
            User.email.ilike(like)
            | User.first_name.ilike(like)
            | User.last_name.ilike(like)
        )
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()

    items = []
    for u in users:
        app_count_res = await session.execute(
            select(func.count()).select_from(Application).where(
                Application.applicant_id == u.id
            )
        )
        app_count = app_count_res.scalar() or 0

        items.append(
            AdminUserResponse(
                id=str(u.id),
                keycloak_id=u.keycloak_id,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                phone=u.phone,
                role=u.role,
                is_active=u.is_active,
                last_login_at=u.last_login_at,
                application_count=app_count,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
        )

    return AdminUserListResponse(items=items, total=total)


@router.get("/users/{user_id}", response_model=AdminUserResponse)
@require_role(["admin"])
async def get_user(
    user_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """Get a user's details."""
    result = await session.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")

    app_count_res = await session.execute(
        select(func.count()).select_from(Application).where(
            Application.applicant_id == u.id
        )
    )
    app_count = app_count_res.scalar() or 0

    return AdminUserResponse(
        id=str(u.id),
        keycloak_id=u.keycloak_id,
        email=u.email,
        first_name=u.first_name,
        last_name=u.last_name,
        phone=u.phone,
        role=u.role,
        is_active=u.is_active,
        last_login_at=u.last_login_at,
        application_count=app_count,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


@router.put("/users/{user_id}", response_model=AdminUserResponse)
@require_role(["admin"])
async def update_user(
    user_id: UUID,
    data: AdminUserUpdate,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """Update a user's role or active status."""
    result = await session.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")

    valid_roles = {"applicant", "loan_servicer", "admin"}
    if data.role is not None:
        if data.role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
            )
        u.role = data.role
    if data.is_active is not None:
        u.is_active = data.is_active

    await session.commit()
    await session.refresh(u)

    app_count_res = await session.execute(
        select(func.count()).select_from(Application).where(
            Application.applicant_id == u.id
        )
    )
    app_count = app_count_res.scalar() or 0

    return AdminUserResponse(
        id=str(u.id),
        keycloak_id=u.keycloak_id,
        email=u.email,
        first_name=u.first_name,
        last_name=u.last_name,
        phone=u.phone,
        role=u.role,
        is_active=u.is_active,
        last_login_at=u.last_login_at,
        application_count=app_count,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


# ── System Health ────────────────────────────────────────────────────────

@router.get("/health", response_model=SystemHealthResponse)
@require_role(["admin"])
async def get_system_health(
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SystemHealthResponse:
    """Detailed system health for admin dashboard."""
    components: list[ComponentHealth] = []

    # Database
    try:
        start = time.time()
        await session.execute(select(func.count()).select_from(User))
        latency = (time.time() - start) * 1000
        components.append(ComponentHealth(
            name="PostgreSQL",
            status="healthy",
            message="Database connected",
            latency_ms=round(latency, 1),
        ))
    except Exception as e:
        components.append(ComponentHealth(
            name="PostgreSQL",
            status="unhealthy",
            message=f"Database error: {str(e)[:100]}",
        ))

    # Redis
    try:
        import redis.asyncio as aioredis

        start = time.time()
        r = aioredis.Redis.from_url(settings.REDIS_URL)
        await r.ping()
        info = await r.info("memory")
        await r.aclose()
        latency = (time.time() - start) * 1000
        components.append(ComponentHealth(
            name="Redis",
            status="healthy",
            message="Redis connected",
            latency_ms=round(latency, 1),
            details={"used_memory_human": info.get("used_memory_human", "N/A")},
        ))
    except Exception as e:
        components.append(ComponentHealth(
            name="Redis",
            status="unhealthy",
            message=f"Redis error: {str(e)[:100]}",
        ))

    # MinIO
    try:
        from ..services.storage import check_health as check_minio
        start = time.time()
        minio_health = await check_minio()
        latency = (time.time() - start) * 1000
        components.append(ComponentHealth(
            name="MinIO Storage",
            status=minio_health.get("status", "unknown"),
            message=f"Bucket: {minio_health.get('bucket', 'N/A')}",
            latency_ms=round(latency, 1),
        ))
    except Exception as e:
        components.append(ComponentHealth(
            name="MinIO Storage",
            status="unhealthy",
            message=f"MinIO error: {str(e)[:100]}",
        ))

    # Celery
    try:
        from ..worker.celery_app import celery_app

        inspector = celery_app.control.inspect(timeout=2.0)
        active = inspector.active()
        if active:
            components.append(ComponentHealth(
                name="Celery Workers",
                status="healthy",
                message=f"{len(active)} worker(s) connected",
                details={"workers": list(active.keys())},
            ))
        else:
            components.append(ComponentHealth(
                name="Celery Workers",
                status="degraded",
                message="No workers responding",
            ))
    except Exception as e:
        components.append(ComponentHealth(
            name="Celery Workers",
            status="unhealthy",
            message=f"Celery error: {str(e)[:100]}",
        ))

    # Keycloak
    try:
        import httpx

        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(settings.keycloak_openid_config_url)
        latency = (time.time() - start) * 1000
        if resp.status_code == 200:
            components.append(ComponentHealth(
                name="Keycloak",
                status="healthy",
                message="Auth service connected",
                latency_ms=round(latency, 1),
            ))
        else:
            components.append(ComponentHealth(
                name="Keycloak",
                status="degraded",
                message=f"HTTP {resp.status_code}",
                latency_ms=round(latency, 1),
            ))
    except Exception as e:
        components.append(ComponentHealth(
            name="Keycloak",
            status="unhealthy",
            message=f"Keycloak error: {str(e)[:100]}",
        ))

    # LLM Providers
    llm_result = await session.execute(
        select(LLMConfig).where(LLMConfig.is_active == True)  # noqa: E712
    )
    for config in llm_result.scalars().all():
        components.append(ComponentHealth(
            name=f"LLM: {config.provider}",
            status="healthy" if config.is_active else "degraded",
            message=f"Model: {config.default_model}",
            details={
                "is_default": config.is_default,
                "rate_limit_rpm": config.rate_limit_rpm,
            },
        ))

    # Overall status
    statuses = [c.status for c in components]
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "unhealthy"
    else:
        overall = "degraded"

    return SystemHealthResponse(
        overall_status=overall,
        components=components,
        checked_at=datetime.now(UTC),
    )
