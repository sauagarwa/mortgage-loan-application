"""
Servicer dashboard Pydantic schemas.
"""

from pydantic import BaseModel

from .applications import ApplicationListItem


class RiskDistribution(BaseModel):
    """Distribution of applications by risk band."""

    low: int = 0
    medium: int = 0
    high: int = 0
    very_high: int = 0


class DashboardStatsResponse(BaseModel):
    """Servicer dashboard statistics."""

    pending_review: int = 0
    in_progress: int = 0
    decided_today: int = 0
    average_processing_time_hours: float | None = None
    approval_rate: float | None = None
    risk_distribution: RiskDistribution = RiskDistribution()
    recent_applications: list[ApplicationListItem] = []
