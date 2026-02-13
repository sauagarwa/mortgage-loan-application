"""
Servicer dashboard routes - statistics and queue management.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import Application, Decision, RiskAssessment, User, get_db

from ..core.security import TokenUser, get_current_user, require_role
from ..schemas.admin import (
    AnalyticsResponse,
    ApprovalRateByBand,
    OverrideStats,
    ProcessingTimeStats,
    VolumeByStatus,
)
from ..schemas.applications import ApplicationListItem
from ..schemas.servicer import DashboardStatsResponse, RiskDistribution

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStatsResponse)
@require_role(["loan_servicer", "admin"])
async def get_dashboard_stats(
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DashboardStatsResponse:
    """Get servicer dashboard statistics."""

    # Count pending review (submitted + under_review)
    pending_result = await session.execute(
        select(func.count()).select_from(Application).where(
            Application.status.in_(["submitted", "under_review"])
        )
    )
    pending_review = pending_result.scalar() or 0

    # Count in progress (risk_assessment_in_progress, documents_processing, additional_info_requested)
    in_progress_result = await session.execute(
        select(func.count()).select_from(Application).where(
            Application.status.in_([
                "risk_assessment_in_progress",
                "documents_processing",
                "additional_info_requested",
            ])
        )
    )
    in_progress = in_progress_result.scalar() or 0

    # Count decided today
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    decided_today_result = await session.execute(
        select(func.count()).select_from(Decision).where(
            Decision.decided_at >= today_start
        )
    )
    decided_today = decided_today_result.scalar() or 0

    # Calculate approval rate (last 30 days)
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    total_decisions_result = await session.execute(
        select(func.count()).select_from(Decision).where(
            Decision.decided_at >= thirty_days_ago
        )
    )
    total_decisions = total_decisions_result.scalar() or 0

    approval_rate = None
    if total_decisions > 0:
        approved_result = await session.execute(
            select(func.count()).select_from(Decision).where(
                and_(
                    Decision.decided_at >= thirty_days_ago,
                    Decision.decision.in_(["approved", "conditionally_approved"]),
                )
            )
        )
        approved_count = approved_result.scalar() or 0
        approval_rate = round(approved_count / total_decisions, 2)

    # Average processing time (submitted_at to decided_at for decided applications)
    avg_time_result = await session.execute(
        select(
            func.avg(
                func.extract("epoch", Application.decided_at)
                - func.extract("epoch", Application.submitted_at)
            )
        )
        .select_from(Application)
        .where(
            and_(
                Application.decided_at.isnot(None),
                Application.submitted_at.isnot(None),
            )
        )
    )
    avg_seconds = avg_time_result.scalar()
    avg_hours = round(avg_seconds / 3600, 1) if avg_seconds else None

    # Risk distribution
    risk_dist = RiskDistribution()
    risk_result = await session.execute(
        select(RiskAssessment.risk_band, func.count())
        .where(RiskAssessment.status == "completed")
        .group_by(RiskAssessment.risk_band)
    )
    for band, count in risk_result.all():
        if band == "low":
            risk_dist.low = count
        elif band == "medium":
            risk_dist.medium = count
        elif band == "high":
            risk_dist.high = count
        elif band == "very_high":
            risk_dist.very_high = count

    # Recent applications (last 10 submitted)
    recent_result = await session.execute(
        select(Application)
        .options(
            selectinload(Application.loan_product),
            selectinload(Application.applicant),
            selectinload(Application.assigned_servicer),
            selectinload(Application.risk_assessments),
        )
        .where(Application.status != "draft")
        .order_by(Application.submitted_at.desc())
        .limit(10)
    )
    recent_apps = recent_result.scalars().unique().all()

    recent_items = []
    for app in recent_apps:
        applicant_name = None
        if app.applicant:
            applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}"

        servicer_name = None
        if app.assigned_servicer:
            servicer_name = f"{app.assigned_servicer.first_name} {app.assigned_servicer.last_name}"

        risk_score = None
        risk_band = None
        if app.risk_assessments:
            latest_ra = sorted(
                app.risk_assessments, key=lambda r: r.created_at, reverse=True
            )[0]
            risk_score = float(latest_ra.overall_score) if latest_ra.overall_score else None
            risk_band = latest_ra.risk_band

        recent_items.append(
            ApplicationListItem(
                id=str(app.id),
                application_number=app.application_number,
                status=app.status,
                applicant_name=applicant_name,
                loan_type=app.loan_product.name if app.loan_product else None,
                loan_amount=float(app.loan_amount) if app.loan_amount else None,
                risk_score=risk_score,
                risk_band=risk_band,
                submitted_at=app.submitted_at,
                created_at=app.created_at,
                assigned_servicer=servicer_name,
            )
        )

    return DashboardStatsResponse(
        pending_review=pending_review,
        in_progress=in_progress,
        decided_today=decided_today,
        average_processing_time_hours=avg_hours,
        approval_rate=approval_rate,
        risk_distribution=risk_dist,
        recent_applications=recent_items,
    )


@router.get("/analytics", response_model=AnalyticsResponse)
@require_role(["loan_servicer", "admin"])
async def get_analytics(
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AnalyticsResponse:
    """Get detailed analytics for servicer reporting."""

    # Total applications and decisions
    total_apps = (await session.execute(
        select(func.count()).select_from(Application).where(Application.status != "draft")
    )).scalar() or 0

    total_decisions = (await session.execute(
        select(func.count()).select_from(Decision)
    )).scalar() or 0

    # Overall approval rate
    approval_rate_overall = None
    if total_decisions > 0:
        approved_count = (await session.execute(
            select(func.count()).select_from(Decision).where(
                Decision.decision.in_(["approved", "conditionally_approved"])
            )
        )).scalar() or 0
        approval_rate_overall = round(approved_count / total_decisions, 4)

    # Approval rate by risk band
    approval_by_band: list[ApprovalRateByBand] = []
    band_result = await session.execute(
        select(
            RiskAssessment.risk_band,
            func.count(Decision.id).label("total"),
            func.count(
                func.nullif(
                    Decision.decision.notin_(["approved", "conditionally_approved"]),
                    True,
                )
            ).label("approved"),
        )
        .select_from(Decision)
        .join(RiskAssessment, RiskAssessment.application_id == Decision.application_id)
        .where(RiskAssessment.status == "completed", RiskAssessment.risk_band.isnot(None))
        .group_by(RiskAssessment.risk_band)
    )
    for band, total, approved in band_result.all():
        approval_by_band.append(ApprovalRateByBand(
            risk_band=band,
            total=total,
            approved=approved,
            rate=round(approved / total, 4) if total > 0 else None,
        ))

    # Processing time stats
    time_result = await session.execute(
        select(
            func.avg(
                func.extract("epoch", Application.decided_at)
                - func.extract("epoch", Application.submitted_at)
            ),
            func.min(
                func.extract("epoch", Application.decided_at)
                - func.extract("epoch", Application.submitted_at)
            ),
            func.max(
                func.extract("epoch", Application.decided_at)
                - func.extract("epoch", Application.submitted_at)
            ),
        )
        .select_from(Application)
        .where(
            Application.decided_at.isnot(None),
            Application.submitted_at.isnot(None),
        )
    )
    row = time_result.one()
    processing_time = ProcessingTimeStats(
        average_hours=round(row[0] / 3600, 2) if row[0] else None,
        min_hours=round(row[1] / 3600, 2) if row[1] else None,
        max_hours=round(row[2] / 3600, 2) if row[2] else None,
    )

    # Volume by status
    volume_result = await session.execute(
        select(Application.status, func.count())
        .where(Application.status != "draft")
        .group_by(Application.status)
    )
    volume_by_status = [
        VolumeByStatus(status=s, count=c)
        for s, c in volume_result.all()
    ]

    # Override stats
    override_total = (await session.execute(
        select(func.count()).select_from(Decision).where(
            Decision.servicer_agreed_with_ai == False  # noqa: E712
        )
    )).scalar() or 0

    ai_approve_deny = (await session.execute(
        select(func.count()).select_from(Decision).where(
            Decision.ai_recommendation.in_(["approve", "approved"]),
            Decision.decision == "denied",
        )
    )).scalar() or 0

    ai_deny_approve = (await session.execute(
        select(func.count()).select_from(Decision).where(
            Decision.ai_recommendation.in_(["deny", "denied"]),
            Decision.decision.in_(["approved", "conditionally_approved"]),
        )
    )).scalar() or 0

    override_stats = OverrideStats(
        total_decisions=total_decisions,
        total_overrides=override_total,
        override_rate=round(override_total / total_decisions, 4) if total_decisions > 0 else None,
        ai_approve_servicer_deny=ai_approve_deny,
        ai_deny_servicer_approve=ai_deny_approve,
        ai_conditional_servicer_different=max(0, override_total - ai_approve_deny - ai_deny_approve),
    )

    return AnalyticsResponse(
        approval_rate_overall=approval_rate_overall,
        approval_rate_by_band=approval_by_band,
        processing_time=processing_time,
        volume_by_status=volume_by_status,
        override_stats=override_stats,
        total_applications=total_apps,
        total_decisions=total_decisions,
    )
