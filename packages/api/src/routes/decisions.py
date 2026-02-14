"""
Decision routes - loan decisions and risk assessment viewing.
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import (
    Application,
    CreditReport,
    Decision,
    InfoRequest,
    Notification,
    RiskAssessment,
    RiskDimensionScore,
    User,
    get_db,
)

from ..core.security import TokenUser, get_current_user, require_role
from ..services.websocket_manager import publish_event
from ..schemas.credit_report import (
    CreditReportResponse,
    CollectionResponse,
    FraudAlertResponse,
    InquiryResponse,
    PublicRecordResponse,
    TradelineResponse,
)
from ..schemas.decisions import (
    DecisionCreate,
    DecisionResponse,
    InfoRequestCreate,
    InfoRequestResponse,
    RiskAssessmentApplicantView,
    RiskAssessmentResponse,
    RiskDimensionScoreResponse,
)

router = APIRouter()


async def _get_user_record(user: TokenUser, session: AsyncSession) -> User:
    """Get the local user record."""
    result = await session.execute(
        select(User).where(User.keycloak_id == user.keycloak_id)
    )
    db_user = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User record not found. Please call /api/v1/auth/me first.",
        )
    return db_user


async def _verify_application_access(
    application_id: UUID, user: TokenUser, session: AsyncSession
) -> Application:
    """Verify the user has access to the application."""
    result = await session.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()

    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if user.is_applicant and not user.is_loan_servicer and not user.is_admin:
        db_user = await _get_user_record(user, session)
        if app.applicant_id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this application",
            )

    return app


@router.get(
    "/{application_id}/risk-assessment",
    response_model=RiskAssessmentResponse | RiskAssessmentApplicantView,
)
async def get_risk_assessment(
    application_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get risk assessment for an application.

    Servicers/admins get the full view; applicants get a simplified summary.
    """
    app = await _verify_application_access(application_id, user, session)

    # Get latest completed risk assessment
    result = await session.execute(
        select(RiskAssessment)
        .options(selectinload(RiskAssessment.dimension_scores))
        .where(RiskAssessment.application_id == application_id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(1)
    )
    ra = result.scalar_one_or_none()

    if ra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk assessment found for this application",
        )

    # Applicant gets simplified view
    if user.is_applicant and not user.is_loan_servicer and not user.is_admin:
        positive_highlights = []
        areas_of_concern = []

        for dim in ra.dimension_scores or []:
            positive_highlights.extend(dim.positive_factors or [])
            areas_of_concern.extend(dim.risk_factors or [])

        return RiskAssessmentApplicantView(
            id=str(ra.id),
            status=ra.status,
            overall_score=float(ra.overall_score) if ra.overall_score else None,
            risk_band=ra.risk_band,
            recommendation=ra.recommendation,
            summary=ra.summary,
            positive_highlights=positive_highlights[:5],
            areas_of_concern=areas_of_concern[:3],
        )

    # Full view for servicers/admins
    dimensions = [
        RiskDimensionScoreResponse(
            name=dim.dimension_name,
            score=float(dim.score),
            weight=float(dim.weight),
            weighted_score=float(dim.weighted_score),
            agent=dim.agent_name,
            positive_factors=dim.positive_factors or [],
            risk_factors=dim.risk_factors or [],
            mitigating_factors=dim.mitigating_factors or [],
            explanation=dim.explanation,
        )
        for dim in (ra.dimension_scores or [])
    ]

    processing_metadata = None
    if ra.started_at or ra.completed_at:
        duration = None
        if ra.started_at and ra.completed_at:
            duration = (ra.completed_at - ra.started_at).total_seconds()
        processing_metadata = {
            "started_at": ra.started_at.isoformat() if ra.started_at else None,
            "completed_at": ra.completed_at.isoformat() if ra.completed_at else None,
            "duration_seconds": duration,
            "llm_provider": ra.llm_provider,
            "model": ra.llm_model,
            "total_tokens_used": ra.total_tokens,
        }

    return RiskAssessmentResponse(
        id=str(ra.id),
        application_id=str(ra.application_id),
        status=ra.status,
        overall_score=float(ra.overall_score) if ra.overall_score else None,
        risk_band=ra.risk_band,
        confidence=float(ra.confidence) if ra.confidence else None,
        recommendation=ra.recommendation,
        summary=ra.summary,
        dimensions=dimensions,
        conditions=ra.conditions or [],
        processing_metadata=processing_metadata,
    )


@router.get("/{application_id}/credit-report", response_model=CreditReportResponse)
@require_role(["loan_servicer", "admin"])
async def get_credit_report(
    application_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CreditReportResponse:
    """Get the credit bureau report for an application.

    Only available to servicers and admins.
    """
    await _verify_application_access(application_id, user, session)

    # Get latest credit report
    result = await session.execute(
        select(CreditReport)
        .where(CreditReport.application_id == application_id)
        .order_by(CreditReport.created_at.desc())
        .limit(1)
    )
    cr = result.scalar_one_or_none()

    if cr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No credit report found for this application",
        )

    return CreditReportResponse(
        id=str(cr.id),
        application_id=str(cr.application_id),
        credit_score=cr.credit_score,
        score_model=cr.score_model,
        score_factors=cr.score_factors or [],
        tradelines=[
            TradelineResponse(**t) for t in (cr.tradelines or [])
        ],
        public_records=[
            PublicRecordResponse(**r) for r in (cr.public_records or [])
        ],
        inquiries=[
            InquiryResponse(**i) for i in (cr.inquiries or [])
        ],
        collections=[
            CollectionResponse(**c) for c in (cr.collections or [])
        ],
        fraud_alerts=[
            FraudAlertResponse(**a) for a in (cr.fraud_alerts or [])
        ],
        fraud_score=cr.fraud_score,
        total_accounts=cr.total_accounts,
        open_accounts=cr.open_accounts,
        credit_utilization=float(cr.credit_utilization) if cr.credit_utilization else None,
        oldest_account_months=cr.oldest_account_months,
        avg_account_age_months=cr.avg_account_age_months,
        on_time_payments_pct=float(cr.on_time_payments_pct) if cr.on_time_payments_pct else None,
        late_payments_30d=cr.late_payments_30d,
        late_payments_60d=cr.late_payments_60d,
        late_payments_90d=cr.late_payments_90d,
        pulled_at=cr.pulled_at.isoformat() if cr.pulled_at else None,
    )


@router.get("/{application_id}/decision", response_model=DecisionResponse)
async def get_decision(
    application_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DecisionResponse:
    """Get the decision for an application."""
    await _verify_application_access(application_id, user, session)

    result = await session.execute(
        select(Decision)
        .options(selectinload(Decision.decided_by_user))
        .where(Decision.application_id == application_id)
    )
    decision = result.scalar_one_or_none()

    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No decision found for this application",
        )

    decided_by_name = None
    decided_by_role = None
    if decision.decided_by_user:
        decided_by_name = (
            f"{decision.decided_by_user.first_name} {decision.decided_by_user.last_name}"
        )
        decided_by_role = decision.decided_by_user.role

    return DecisionResponse(
        id=str(decision.id),
        application_id=str(decision.application_id),
        decision=decision.decision,
        ai_recommendation=decision.ai_recommendation,
        servicer_agreed_with_ai=decision.servicer_agreed_with_ai,
        override_justification=decision.override_justification,
        conditions=decision.conditions or [],
        adverse_action_reasons=decision.adverse_action_reasons or [],
        interest_rate=float(decision.interest_rate) if decision.interest_rate else None,
        approved_loan_amount=float(decision.approved_loan_amount) if decision.approved_loan_amount else None,
        approved_term_years=decision.approved_term_years,
        monthly_payment=float(decision.monthly_payment) if decision.monthly_payment else None,
        notes=decision.notes,
        decided_by_name=decided_by_name,
        decided_by_role=decided_by_role,
        decided_at=decision.decided_at,
    )


@router.post("/{application_id}/decision", response_model=DecisionResponse, status_code=201)
@require_role(["loan_servicer", "admin"])
async def create_decision(
    application_id: UUID,
    data: DecisionCreate,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DecisionResponse:
    """Create a loan decision (approve, deny, or conditionally approve)."""
    app = await _verify_application_access(application_id, user, session)

    # Verify application is in a decidable state
    decidable_statuses = {"submitted", "under_review", "risk_assessment_in_progress"}
    if app.status not in decidable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot make a decision on an application with status '{app.status}'",
        )

    # Check if decision already exists
    existing = await session.execute(
        select(Decision).where(Decision.application_id == application_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A decision has already been made for this application",
        )

    valid_decisions = {"approved", "denied", "conditionally_approved"}
    if data.decision not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}",
        )

    db_user = await _get_user_record(user, session)

    # Get latest risk assessment for AI recommendation
    ra_result = await session.execute(
        select(RiskAssessment)
        .where(RiskAssessment.application_id == application_id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(1)
    )
    latest_ra = ra_result.scalar_one_or_none()

    ai_recommendation = latest_ra.recommendation if latest_ra else None
    servicer_agreed = None
    if ai_recommendation:
        servicer_agreed = not data.override_ai_recommendation

    # Calculate monthly payment if approving
    monthly_payment = None
    if data.decision in ("approved", "conditionally_approved") and data.interest_rate:
        loan_amt = data.approved_loan_amount or (float(app.loan_amount) if app.loan_amount else 0)
        term = data.approved_term_years or (app.loan_product.term_years if app.loan_product else 30)
        if loan_amt > 0:
            monthly_rate = data.interest_rate / 100 / 12
            n_payments = term * 12
            if monthly_rate > 0:
                monthly_payment = loan_amt * (
                    monthly_rate * (1 + monthly_rate) ** n_payments
                ) / ((1 + monthly_rate) ** n_payments - 1)

    now = datetime.now(UTC)
    decision = Decision(
        application_id=application_id,
        risk_assessment_id=latest_ra.id if latest_ra else None,
        decided_by=db_user.id,
        decision=data.decision,
        ai_recommendation=ai_recommendation,
        servicer_agreed_with_ai=servicer_agreed,
        override_justification=data.override_justification if data.override_ai_recommendation else None,
        conditions=data.conditions,
        adverse_action_reasons=data.adverse_action_reasons,
        interest_rate=data.interest_rate,
        approved_loan_amount=data.approved_loan_amount,
        approved_term_years=data.approved_term_years,
        monthly_payment=monthly_payment,
        notes=data.notes,
        decided_at=now,
    )
    session.add(decision)

    # Update application status
    app.status = data.decision
    app.decided_at = now

    # Create notification for applicant
    decision_text = {
        "approved": "approved",
        "denied": "denied",
        "conditionally_approved": "conditionally approved",
    }
    notification = Notification(
        user_id=app.applicant_id,
        type="decision_made",
        title=f"Application {decision_text.get(data.decision, data.decision)}",
        message=(
            f"Your mortgage application {app.application_number} has been "
            f"{decision_text.get(data.decision, data.decision)}."
        ),
        application_id=application_id,
    )
    session.add(notification)

    await session.commit()
    await session.refresh(decision)

    # Notify via WebSocket
    await publish_event(f"application:{application_id}", {
        "type": "decision_made",
        "data": {
            "application_id": str(application_id),
            "decision": data.decision,
        },
    })

    return DecisionResponse(
        id=str(decision.id),
        application_id=str(decision.application_id),
        decision=decision.decision,
        ai_recommendation=decision.ai_recommendation,
        servicer_agreed_with_ai=decision.servicer_agreed_with_ai,
        override_justification=decision.override_justification,
        conditions=decision.conditions or [],
        adverse_action_reasons=decision.adverse_action_reasons or [],
        interest_rate=float(decision.interest_rate) if decision.interest_rate else None,
        approved_loan_amount=float(decision.approved_loan_amount) if decision.approved_loan_amount else None,
        approved_term_years=decision.approved_term_years,
        monthly_payment=round(monthly_payment, 2) if monthly_payment else None,
        notes=decision.notes,
        decided_by_name=f"{db_user.first_name} {db_user.last_name}",
        decided_by_role=db_user.role,
        decided_at=decision.decided_at,
    )


@router.post("/{application_id}/request-info", response_model=InfoRequestResponse)
@require_role(["loan_servicer", "admin"])
async def request_additional_info(
    application_id: UUID,
    data: InfoRequestCreate,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> InfoRequestResponse:
    """Request additional information from the applicant."""
    app = await _verify_application_access(application_id, user, session)

    if app.status in ("approved", "denied", "withdrawn"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot request info for an application with status '{app.status}'",
        )

    db_user = await _get_user_record(user, session)

    info_request = InfoRequest(
        application_id=application_id,
        requested_by=db_user.id,
        requested_items=[item.model_dump() for item in data.requested_items],
        due_date=data.due_date,
        status="pending",
    )
    session.add(info_request)

    # Update application status
    app.status = "additional_info_requested"

    # Notify applicant
    notification = Notification(
        user_id=app.applicant_id,
        type="info_requested",
        title="Additional information requested",
        message=(
            f"Additional information has been requested for your application "
            f"{app.application_number}. Please review and respond."
        ),
        application_id=application_id,
    )
    session.add(notification)

    await session.commit()

    return InfoRequestResponse(
        application_id=str(application_id),
        status="additional_info_requested",
        requested_items=data.requested_items,
        due_date=data.due_date,
        message="Applicant has been notified of the information request.",
    )
