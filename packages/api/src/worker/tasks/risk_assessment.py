"""
Celery tasks for risk assessment.

Runs multi-dimensional risk analysis on submitted mortgage applications
using AI agent pipeline with rule-based fallback.
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from db import Application, RiskAssessment, RiskDimensionScore

from ..celery_app import celery_app
from ..db import get_sync_session
from ...agents.base import ApplicationData
from ...agents.pipeline import run_pipeline
from ...services.websocket_manager import publish_event_sync

logger = logging.getLogger(__name__)

# Rule-based dimension scorers (kept as fallback)
# ------------------------------------------------

RISK_BANDS = [
    (80, "low"),
    (60, "medium"),
    (40, "high"),
    (0, "critical"),
]

DIMENSION_WEIGHTS = {
    "credit_profile": 0.25,
    "income_stability": 0.20,
    "debt_to_income": 0.20,
    "down_payment": 0.15,
    "employment_history": 0.10,
    "property_assessment": 0.10,
}


def _get_risk_band(score: float) -> str:
    for threshold, band in RISK_BANDS:
        if score >= threshold:
            return band
    return "critical"


def _score_credit_profile(application: Application) -> dict[str, Any]:
    financial = application.financial_info or {}
    credit_score = financial.get("credit_score", 0)
    score = 0.0
    positive, risks, mitigating = [], [], []

    if credit_score >= 760:
        score, positive = 95.0, ["Excellent credit score (760+)"]
    elif credit_score >= 700:
        score, positive = 80.0, ["Good credit score (700-759)"]
    elif credit_score >= 660:
        score = 65.0
        positive.append("Fair credit score (660-699)")
        risks.append("Credit score below preferred threshold of 700")
    elif credit_score >= 620:
        score = 45.0
        risks.append("Below-average credit score (620-659)")
        mitigating.append("Score meets minimum FHA requirements")
    elif credit_score > 0:
        score = 25.0
        risks.append(f"Low credit score ({credit_score})")
    else:
        score = 30.0
        risks.append("Credit score not provided")

    declarations = application.declarations or {}
    if declarations.get("has_bankruptcy"):
        score = max(score - 20, 10)
        risks.append("History of bankruptcy declared")
    if declarations.get("has_foreclosure"):
        score = max(score - 25, 10)
        risks.append("History of foreclosure declared")

    return {"score": score, "positive_factors": positive, "risk_factors": risks,
            "mitigating_factors": mitigating,
            "explanation": f"Credit profile based on score of {credit_score}."}


def _score_income_stability(application: Application) -> dict[str, Any]:
    employment = application.employment_info or {}
    score, positive, risks, mitigating = 50.0, [], [], []
    emp_status = employment.get("employment_status", "").lower()
    years = employment.get("years_at_job", 0)

    if emp_status == "employed":
        score += 15; positive.append("Currently employed")
    elif emp_status == "self_employed":
        score += 5; risks.append("Self-employed income may be variable")
    elif emp_status == "retired":
        score += 10; positive.append("Retired with stable income")

    if years >= 5: score += 20; positive.append(f"Long tenure ({years}+ years)")
    elif years >= 2: score += 10; positive.append(f"Stable employment ({years} years)")
    elif years > 0: risks.append(f"Short tenure ({years} year(s))")

    if application.loan_amount and employment.get("annual_income", 0) > 0:
        ratio = float(employment["annual_income"]) / float(application.loan_amount)
        if ratio >= 0.5: score += 15; positive.append("Strong income-to-loan ratio")
        elif ratio >= 0.25: score += 5

    return {"score": min(score, 100), "positive_factors": positive, "risk_factors": risks,
            "mitigating_factors": mitigating, "explanation": "Income stability assessment."}


def _score_debt_to_income(application: Application) -> dict[str, Any]:
    dti = float(application.dti_ratio) if application.dti_ratio else None
    score, positive, risks, mitigating = 50.0, [], [], []

    if dti is not None:
        if dti <= 28: score = 95.0; positive.append(f"Excellent DTI ({dti:.1f}%)")
        elif dti <= 36: score = 80.0; positive.append(f"Good DTI ({dti:.1f}%)")
        elif dti <= 43: score = 60.0; risks.append(f"DTI ({dti:.1f}%) near limit")
        elif dti <= 50: score = 35.0; risks.append(f"High DTI ({dti:.1f}%)")
        else: score = 15.0; risks.append(f"Very high DTI ({dti:.1f}%)")
    else:
        risks.append("Unable to calculate DTI")

    return {"score": score, "positive_factors": positive, "risk_factors": risks,
            "mitigating_factors": mitigating,
            "explanation": f"DTI ratio: {dti:.1f}%." if dti else "DTI unavailable."}


def _score_down_payment(application: Application) -> dict[str, Any]:
    score, positive, risks, mitigating = 50.0, [], [], []
    dp = float(application.down_payment) if application.down_payment else 0
    pp = (application.property_info or {}).get("purchase_price", 0)

    if pp and dp:
        pct = (dp / pp) * 100
        if pct >= 20: score = 95.0; positive.append(f"Strong down payment ({pct:.1f}%)")
        elif pct >= 10: score = 75.0; positive.append(f"Moderate ({pct:.1f}%)")
        elif pct >= 5: score = 55.0; risks.append(f"Low down payment ({pct:.1f}%)")
        elif pct >= 3.5: score = 40.0; risks.append(f"Minimum down payment ({pct:.1f}%)")
        else: score = 20.0; risks.append(f"Below minimum ({pct:.1f}%)")
    else:
        risks.append("Down payment data unavailable")

    return {"score": score, "positive_factors": positive, "risk_factors": risks,
            "mitigating_factors": mitigating, "explanation": "Down payment assessment."}


def _score_employment_history(application: Application) -> dict[str, Any]:
    emp = application.employment_info or {}
    score, positive, risks, mitigating = 50.0, [], [], []

    if emp.get("employer_name") and emp.get("job_title"):
        score += 10; positive.append("Complete employment info")
    if emp.get("employment_status") == "employed" and emp.get("years_at_job", 0) >= 2:
        score += 25; positive.append("Stable employment")
    if emp.get("previous_employer"):
        score += 10; positive.append("History documented")

    return {"score": min(score, 100), "positive_factors": positive, "risk_factors": risks,
            "mitigating_factors": mitigating, "explanation": "Employment history assessment."}


def _score_property_assessment(application: Application) -> dict[str, Any]:
    prop = application.property_info or {}
    score, positive, risks, mitigating = 50.0, [], [], []

    ptype = prop.get("property_type", "")
    if ptype in ("single_family", "townhouse"):
        score += 20; positive.append(f"Standard type ({ptype.replace('_', ' ')})")
    elif ptype == "condo":
        score += 15; positive.append("Condominium")

    usage = prop.get("usage_type", "")
    if usage == "primary_residence":
        score += 20; positive.append("Primary residence")
    elif usage == "investment":
        risks.append("Investment property")

    if prop.get("purchase_price", 0) >= 100000:
        score += 10; positive.append("Property value supports collateral")

    return {"score": min(score, 100), "positive_factors": positive, "risk_factors": risks,
            "mitigating_factors": mitigating, "explanation": "Property assessment."}


DIMENSION_SCORERS = {
    "credit_profile": _score_credit_profile,
    "income_stability": _score_income_stability,
    "debt_to_income": _score_debt_to_income,
    "down_payment": _score_down_payment,
    "employment_history": _score_employment_history,
    "property_assessment": _score_property_assessment,
}


@celery_app.task(
    bind=True,
    name="src.worker.tasks.risk_assessment.run_risk_assessment",
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
)
def run_risk_assessment(self, application_id: str, use_ai: bool = True) -> dict:
    """Run a full risk assessment on a submitted application.

    Uses the AI agent pipeline when LLM is configured, falling back to
    rule-based scoring otherwise.

    Args:
        application_id: UUID string of the application to assess.
        use_ai: If True, attempts AI agent pipeline; if False, uses rules only.

    Returns:
        Dict with assessment results summary.
    """
    logger.info(f"Starting risk assessment for application {application_id} (ai={use_ai})")
    started_at = datetime.now(UTC)

    # Load application with related data
    with get_sync_session() as session:
        result = session.execute(
            select(Application)
            .options(
                joinedload(Application.documents),
                joinedload(Application.loan_product),
            )
            .where(Application.id == application_id)
        )
        application = result.unique().scalar_one_or_none()

        if application is None:
            logger.error(f"Application {application_id} not found")
            return {"status": "error", "error": "Application not found"}

        if application.status not in ("submitted", "under_review"):
            logger.warning(
                f"Application {application_id} status is {application.status}, skipping"
            )
            return {"status": "skipped", "reason": f"status is {application.status}"}

        # Create risk assessment record
        assessment = RiskAssessment(
            application_id=application.id,
            status="in_progress",
            started_at=started_at,
            attempt_number=self.request.retries + 1,
        )
        session.add(assessment)
        session.commit()
        session.refresh(assessment)
        assessment_id = str(assessment.id)

        # Notify that assessment has started
        publish_event_sync(f"application:{application_id}", {
            "type": "status_change",
            "data": {"status": "risk_assessment_in_progress", "application_id": application_id},
        })

        # Build application data for the pipeline
        app_data = ApplicationData.from_orm(application)

    # Determine if we should use AI agents
    should_use_ai = use_ai
    if should_use_ai:
        from ...core.config import settings
        if not settings.LLM_API_KEY:
            logger.info("No LLM API key configured, falling back to rule-based assessment")
            should_use_ai = False

    # Run the pipeline
    try:
        pipeline_result = run_pipeline(
            data=app_data,
            use_llm=should_use_ai,
        )
    except Exception as exc:
        logger.error(f"Pipeline failed for {application_id}: {exc}")
        # Mark assessment as failed
        with get_sync_session() as session:
            result = session.execute(
                select(RiskAssessment).where(RiskAssessment.id == assessment_id)
            )
            assessment = result.scalar_one()
            assessment.status = "failed"
            assessment.error_message = str(exc)[:500]
            session.commit()
        raise self.retry(exc=exc)

    # Store results in database
    with get_sync_session() as session:
        # Save dimension scores
        for dim_result in pipeline_result.dimension_results:
            dimension_score = RiskDimensionScore(
                risk_assessment_id=assessment_id,
                dimension_name=dim_result.dimension_name,
                agent_name=dim_result.agent_name,
                score=Decimal(str(round(dim_result.score, 2))),
                weight=Decimal(str(dim_result.weight)),
                weighted_score=Decimal(str(round(dim_result.weighted_score, 2))),
                positive_factors=dim_result.positive_factors,
                risk_factors=dim_result.risk_factors,
                mitigating_factors=dim_result.mitigating_factors,
                explanation=dim_result.explanation,
                raw_agent_output=dim_result.raw_llm_output,
                tokens_used=dim_result.tokens_used,
                processing_time_ms=dim_result.processing_time_ms,
            )
            session.add(dimension_score)

        # Update assessment record
        result = session.execute(
            select(RiskAssessment).where(RiskAssessment.id == assessment_id)
        )
        assessment = result.scalar_one()

        assessment.overall_score = Decimal(str(round(pipeline_result.overall_score, 2)))
        assessment.risk_band = pipeline_result.risk_band
        assessment.confidence = Decimal(str(round(pipeline_result.confidence, 2)))
        assessment.recommendation = pipeline_result.recommendation
        assessment.summary = pipeline_result.summary
        assessment.conditions = pipeline_result.conditions
        assessment.status = "completed"
        assessment.completed_at = datetime.now(UTC)
        assessment.total_tokens = pipeline_result.total_tokens

        if should_use_ai:
            from ...core.config import settings
            assessment.llm_provider = settings.LLM_PROVIDER
            assessment.llm_model = settings.LLM_MODEL
        else:
            assessment.llm_provider = "rule_engine"
            assessment.llm_model = "v1.0"

        # Update application status
        app_result = session.execute(
            select(Application).where(Application.id == application_id)
        )
        app = app_result.scalar_one()
        if app.status == "submitted":
            app.status = "under_review"

        session.commit()

    completed_at = datetime.now(UTC)
    processing_time = (completed_at - started_at).total_seconds()

    # Notify that assessment is complete
    publish_event_sync(f"application:{application_id}", {
        "type": "assessment_complete",
        "data": {
            "application_id": application_id,
            "assessment_id": assessment_id,
            "overall_score": round(pipeline_result.overall_score, 2),
            "risk_band": pipeline_result.risk_band,
            "recommendation": pipeline_result.recommendation,
        },
    })

    # Notify servicers about the new assessment
    publish_event_sync("servicer:notifications", {
        "type": "assessment_complete",
        "data": {
            "application_id": application_id,
            "risk_band": pipeline_result.risk_band,
            "recommendation": pipeline_result.recommendation,
        },
    })

    logger.info(
        f"Risk assessment completed for {application_id}: "
        f"score={pipeline_result.overall_score:.1f}, band={pipeline_result.risk_band}, "
        f"rec={pipeline_result.recommendation}, "
        f"agents={pipeline_result.agents_succeeded}/{pipeline_result.agents_succeeded + pipeline_result.agents_failed}, "
        f"tokens={pipeline_result.total_tokens}, time={processing_time:.1f}s"
    )

    return {
        "status": "success",
        "application_id": application_id,
        "assessment_id": assessment_id,
        "overall_score": round(pipeline_result.overall_score, 2),
        "risk_band": pipeline_result.risk_band,
        "recommendation": pipeline_result.recommendation,
        "dimensions_scored": len(pipeline_result.dimension_results),
        "agents_succeeded": pipeline_result.agents_succeeded,
        "agents_failed": pipeline_result.agents_failed,
        "total_tokens": pipeline_result.total_tokens,
        "used_ai": should_use_ai,
        "processing_time_seconds": round(processing_time, 2),
    }
