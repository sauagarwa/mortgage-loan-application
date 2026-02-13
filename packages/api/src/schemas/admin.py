"""
Admin panel Pydantic schemas — LLM config, user management, system health.
"""

from datetime import datetime

from pydantic import BaseModel


# ── LLM Provider Configuration ──────────────────────────────────────────

class LLMProviderResponse(BaseModel):
    """LLM provider config (API key masked)."""

    id: str
    provider: str
    is_active: bool
    is_default: bool
    base_url: str
    api_key_set: bool
    default_model: str
    max_tokens: int
    temperature: float
    rate_limit_rpm: int | None = None
    created_at: datetime
    updated_at: datetime


class LLMProviderUpdate(BaseModel):
    """Update an LLM provider config."""

    is_active: bool | None = None
    is_default: bool | None = None
    base_url: str | None = None
    api_key: str | None = None
    default_model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    rate_limit_rpm: int | None = None


class LLMProviderCreate(BaseModel):
    """Create a new LLM provider config."""

    provider: str
    base_url: str
    api_key: str | None = None
    default_model: str
    max_tokens: int = 4096
    temperature: float = 0.1
    rate_limit_rpm: int = 60
    is_active: bool = False
    is_default: bool = False


class LLMTestResult(BaseModel):
    """Result of testing an LLM provider connection."""

    provider: str
    success: bool
    message: str
    latency_ms: float | None = None


# ── User Management ─────────────────────────────────────────────────────

class AdminUserResponse(BaseModel):
    """User record for admin panel."""

    id: str
    keycloak_id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    application_count: int = 0
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    """Paginated user list."""

    items: list[AdminUserResponse]
    total: int


class AdminUserUpdate(BaseModel):
    """Update a user (admin only)."""

    role: str | None = None
    is_active: bool | None = None


# ── System Health ────────────────────────────────────────────────────────

class ComponentHealth(BaseModel):
    """Health status of a single component."""

    name: str
    status: str  # healthy, degraded, unhealthy
    message: str
    latency_ms: float | None = None
    details: dict | None = None


class SystemHealthResponse(BaseModel):
    """Detailed system health for admin dashboard."""

    overall_status: str  # healthy, degraded, unhealthy
    components: list[ComponentHealth]
    checked_at: datetime


# ── Analytics ────────────────────────────────────────────────────────────

class ApprovalRateByBand(BaseModel):
    """Approval rate for a single risk band."""

    risk_band: str
    total: int
    approved: int
    rate: float | None = None


class OverrideStats(BaseModel):
    """AI override tracking stats."""

    total_decisions: int
    total_overrides: int
    override_rate: float | None = None
    ai_approve_servicer_deny: int = 0
    ai_deny_servicer_approve: int = 0
    ai_conditional_servicer_different: int = 0


class ProcessingTimeStats(BaseModel):
    """Processing time metrics."""

    average_hours: float | None = None
    median_hours: float | None = None
    min_hours: float | None = None
    max_hours: float | None = None


class VolumeByStatus(BaseModel):
    """Application count by status."""

    status: str
    count: int


class AnalyticsResponse(BaseModel):
    """Full analytics response for servicer dashboard."""

    approval_rate_overall: float | None = None
    approval_rate_by_band: list[ApprovalRateByBand] = []
    processing_time: ProcessingTimeStats
    volume_by_status: list[VolumeByStatus] = []
    override_stats: OverrideStats
    total_applications: int = 0
    total_decisions: int = 0
