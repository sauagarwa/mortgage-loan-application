"""
Celery tasks for risk assessment.

Runs multi-dimensional risk analysis on submitted mortgage applications
using AI agent pipeline with rule-based fallback. Includes 10 weighted
dimensions with credit bureau integration and intelligent lending strategies.
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from db import Application, CreditReport, RiskAssessment, RiskDimensionScore

from ..celery_app import celery_app
from ..db import get_sync_session
from ...agents.base import ApplicationData
from ...agents.pipeline import run_pipeline
from ...services.credit_bureau import CreditBureauService
from ...services.websocket_manager import publish_event_sync

logger = logging.getLogger(__name__)

# Rule-based dimension scorers (kept as fallback and for new dimensions)
# -----------------------------------------------------------------------

RISK_BANDS = [
    (80, "low"),
    (60, "medium"),
    (40, "high"),
    (0, "critical"),
]

DIMENSION_WEIGHTS = {
    "credit_profile": 0.12,
    "credit_history_depth": 0.10,
    "payment_history": 0.12,
    "income_stability": 0.12,
    "earning_potential": 0.08,
    "debt_to_income": 0.13,
    "down_payment": 0.08,
    "employment_history": 0.05,
    "property_assessment": 0.05,
    "fraud_risk": 0.05,
    "compensating_factors": 0.10,
}


def _get_risk_band(score: float) -> str:
    for threshold, band in RISK_BANDS:
        if score >= threshold:
            return band
    return "critical"


def _score_credit_profile(
    application: Application, credit_report_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    financial = application.financial_info or {}
    credit_score = financial.get("credit_score", 0)
    score = 0.0
    positive, risks, mitigating = [], [], []

    # Use bureau score if available
    bureau_score = None
    if credit_report_data:
        bureau_score = credit_report_data.get("credit_score")
        if bureau_score:
            credit_score = bureau_score

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

    # Income-adjusted credit evaluation
    employment = application.employment_info or {}
    annual_income = employment.get("annual_income", 0) or 0
    if annual_income >= 150000 and credit_score >= 620:
        adjustment = min(8, (annual_income - 100000) / 25000)
        score = min(100, score + adjustment)
        mitigating.append(
            f"Income-adjusted: high income (${annual_income:,.0f}) offsets credit concerns"
        )

    return {
        "score": score,
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": f"Credit profile based on score of {credit_score}.",
    }


def _score_credit_history_depth(
    application: Application, credit_report_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score based on account age, utilization, and tradeline diversity."""
    score = 50.0
    positive, risks, mitigating = [], [], []

    if not credit_report_data:
        return {
            "score": score,
            "positive_factors": positive,
            "risk_factors": ["No credit bureau data available"],
            "mitigating_factors": mitigating,
            "explanation": "Credit history depth could not be evaluated without bureau data.",
        }

    oldest_months = credit_report_data.get("oldest_account_months", 0)
    avg_age_months = credit_report_data.get("avg_account_age_months", 0)
    total_accounts = credit_report_data.get("total_accounts", 0)
    utilization = credit_report_data.get("credit_utilization", 50)

    # Account age scoring
    oldest_years = oldest_months / 12
    if oldest_years >= 15:
        score += 25
        positive.append(f"Excellent credit history length ({oldest_years:.0f} years)")
    elif oldest_years >= 10:
        score += 20
        positive.append(f"Long credit history ({oldest_years:.0f} years)")
    elif oldest_years >= 5:
        score += 10
        positive.append(f"Moderate credit history ({oldest_years:.1f} years)")
    elif oldest_years >= 2:
        risks.append(f"Short credit history ({oldest_years:.1f} years)")
    else:
        score -= 10
        risks.append(f"Very short credit history ({oldest_months} months)")

    # Average age bonus
    if avg_age_months >= 60:
        score += 10
        positive.append(f"Strong average account age ({avg_age_months // 12} years)")

    # Tradeline diversity
    tradelines = credit_report_data.get("tradelines", [])
    account_types = set()
    for t in tradelines:
        if isinstance(t, dict):
            account_types.add(t.get("account_type", ""))
    if len(account_types) >= 3:
        score += 10
        positive.append(f"Diverse credit mix ({len(account_types)} account types)")
    elif len(account_types) == 1:
        risks.append("Limited credit mix (single account type)")

    # Utilization
    if utilization <= 10:
        score += 10
        positive.append(f"Very low utilization ({utilization:.0f}%)")
    elif utilization <= 30:
        score += 5
        positive.append(f"Good utilization ({utilization:.0f}%)")
    elif utilization >= 70:
        score -= 15
        risks.append(f"High utilization ({utilization:.0f}%) — potential debt accumulation")
    elif utilization >= 50:
        score -= 5
        risks.append(f"Elevated utilization ({utilization:.0f}%)")

    return {
        "score": max(0, min(100, score)),
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": f"Credit history depth: {oldest_years:.1f}yr oldest, "
        f"{avg_age_months // 12}yr avg, {utilization:.0f}% utilization.",
    }


def _score_payment_history(
    application: Application, credit_report_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score based on on-time rate, delinquency severity with recency weighting."""
    score = 50.0
    positive, risks, mitigating = [], [], []

    if not credit_report_data:
        return {
            "score": score,
            "positive_factors": positive,
            "risk_factors": ["No credit bureau data available"],
            "mitigating_factors": mitigating,
            "explanation": "Payment history could not be evaluated without bureau data.",
        }

    on_time_pct = credit_report_data.get("on_time_payments_pct", 100)
    late_30 = credit_report_data.get("late_payments_30d", 0)
    late_60 = credit_report_data.get("late_payments_60d", 0)
    late_90 = credit_report_data.get("late_payments_90d", 0)

    # On-time percentage scoring
    if on_time_pct >= 99:
        score = 95.0
        positive.append(f"Excellent payment history ({on_time_pct:.1f}% on-time)")
    elif on_time_pct >= 97:
        score = 85.0
        positive.append(f"Very good payment history ({on_time_pct:.1f}% on-time)")
    elif on_time_pct >= 95:
        score = 75.0
        positive.append(f"Good payment history ({on_time_pct:.1f}% on-time)")
    elif on_time_pct >= 90:
        score = 55.0
        risks.append(f"Fair payment history ({on_time_pct:.1f}% on-time)")
    else:
        score = 30.0
        risks.append(f"Poor payment history ({on_time_pct:.1f}% on-time)")

    # Severity penalties
    total_lates = late_30 + late_60 + late_90
    if late_90 > 0:
        score -= late_90 * 8
        risks.append(f"{late_90} payment(s) 90+ days late")
    if late_60 > 0:
        score -= late_60 * 5
        risks.append(f"{late_60} payment(s) 60 days late")
    if late_30 > 0:
        score -= late_30 * 2

    # Recency weighting: check if recent tradeline payments are clean
    tradelines = credit_report_data.get("tradelines", [])
    recent_clean = True
    for t in tradelines:
        if isinstance(t, dict):
            history = t.get("payment_history_24m", [])
            # First 12 entries are most recent
            recent_12 = history[:12] if len(history) >= 12 else history
            if any(p != "OK" for p in recent_12):
                recent_clean = False
                break

    if total_lates > 0 and recent_clean:
        score += 10
        mitigating.append(
            "Clean recent payment history (12 months) — past lates are aging off"
        )

    # Recovery trajectory detection
    declarations = application.declarations or {}
    public_records = credit_report_data.get("public_records", [])
    if (declarations.get("has_bankruptcy") or declarations.get("has_foreclosure")) and recent_clean:
        score += 12
        mitigating.append(
            "Recovery trajectory: past derogatory marks with clean recent payments"
        )

    return {
        "score": max(0, min(100, score)),
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": f"Payment history: {on_time_pct:.1f}% on-time, "
        f"{total_lates} late payment(s).",
    }


def _score_income_stability(application: Application, **kwargs) -> dict[str, Any]:
    employment = application.employment_info or {}
    score, positive, risks, mitigating = 50.0, [], [], []
    emp_status = employment.get("employment_status", "").lower()
    years = employment.get("years_at_job", 0) or 0

    if emp_status == "employed":
        score += 15
        positive.append("Currently employed")
    elif emp_status == "self_employed":
        score += 5
        risks.append("Self-employed income may be variable")
    elif emp_status == "retired":
        score += 10
        positive.append("Retired with stable income")

    if years >= 5:
        score += 20
        positive.append(f"Long tenure ({years}+ years)")
    elif years >= 2:
        score += 10
        positive.append(f"Stable employment ({years} years)")
    elif years > 0:
        risks.append(f"Short tenure ({years} year(s))")

    if application.loan_amount and employment.get("annual_income", 0) > 0:
        ratio = float(employment["annual_income"]) / float(application.loan_amount)
        if ratio >= 0.5:
            score += 15
            positive.append("Strong income-to-loan ratio")
        elif ratio >= 0.25:
            score += 5

    return {
        "score": min(score, 100),
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": "Income stability assessment.",
    }


def _score_earning_potential(
    application: Application, credit_report_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score based on income trajectory, field tenure, and income diversification."""
    employment = application.employment_info or {}
    financial = application.financial_info or {}
    score = 50.0
    positive, risks, mitigating = [], [], []

    annual_income = employment.get("annual_income", 0) or 0
    years_at_job = employment.get("years_at_job", 0) or 0
    emp_status = (employment.get("employment_status") or "").lower()

    # Income level assessment
    if annual_income >= 200000:
        score += 20
        positive.append(f"High income (${annual_income:,.0f}/yr)")
    elif annual_income >= 100000:
        score += 15
        positive.append(f"Strong income (${annual_income:,.0f}/yr)")
    elif annual_income >= 60000:
        score += 5
    elif annual_income > 0:
        risks.append(f"Modest income (${annual_income:,.0f}/yr)")

    # Employment stability as proxy for earning trajectory
    if emp_status == "employed" and years_at_job >= 5:
        score += 15
        positive.append(f"Long tenure ({years_at_job} years) suggests career stability")
    elif emp_status == "self_employed":
        if years_at_job >= 2:
            score += 5
            positive.append("Self-employed with 2+ years history")
        else:
            score -= 10
            risks.append("Self-employed less than 2 years — income sustainability uncertain")

    # Income diversification (check for multiple income sources)
    additional_income = financial.get("additional_income", 0) or 0
    if additional_income > 0:
        score += 8
        positive.append(f"Diversified income sources (+${additional_income:,.0f}/yr)")

    # Commission/gig income flag
    job_title = (employment.get("job_title") or "").lower()
    commission_keywords = ["sales", "realtor", "agent", "broker", "freelance", "contractor", "gig"]
    if any(kw in job_title for kw in commission_keywords):
        score -= 5
        risks.append("Commission/variable income role — may require additional verification")

    return {
        "score": max(0, min(100, score)),
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": f"Earning potential: ${annual_income:,.0f}/yr, {years_at_job} years tenure.",
    }


def _score_debt_to_income(application: Application, **kwargs) -> dict[str, Any]:
    dti = float(application.dti_ratio) if application.dti_ratio else None
    score, positive, risks, mitigating = 50.0, [], [], []

    if dti is not None:
        if dti <= 28:
            score = 95.0
            positive.append(f"Excellent DTI ({dti:.1f}%)")
        elif dti <= 36:
            score = 80.0
            positive.append(f"Good DTI ({dti:.1f}%)")
        elif dti <= 43:
            score = 60.0
            risks.append(f"DTI ({dti:.1f}%) near limit")
        elif dti <= 50:
            score = 35.0
            risks.append(f"High DTI ({dti:.1f}%)")
        else:
            score = 15.0
            risks.append(f"Very high DTI ({dti:.1f}%)")

        # Back-end DTI check: if new mortgage would push above 43%
        if dti > 43:
            risks.append(
                f"Back-end DTI ({dti:.1f}%) exceeds 43% QM threshold — "
                "requires compensating factors for approval"
            )
    else:
        risks.append("Unable to calculate DTI")

    return {
        "score": score,
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": f"DTI ratio: {dti:.1f}%." if dti else "DTI unavailable.",
    }


def _score_down_payment(application: Application, **kwargs) -> dict[str, Any]:
    score, positive, risks, mitigating = 50.0, [], [], []
    dp = float(application.down_payment) if application.down_payment else 0
    pp = (application.property_info or {}).get("purchase_price", 0)

    if pp and dp:
        pct = (dp / pp) * 100
        if pct >= 20:
            score = 95.0
            positive.append(f"Strong down payment ({pct:.1f}%)")
        elif pct >= 10:
            score = 75.0
            positive.append(f"Moderate ({pct:.1f}%)")
        elif pct >= 5:
            score = 55.0
            risks.append(f"Low down payment ({pct:.1f}%)")
        elif pct >= 3.5:
            score = 40.0
            risks.append(f"Minimum down payment ({pct:.1f}%)")
        else:
            score = 20.0
            risks.append(f"Below minimum ({pct:.1f}%)")
    else:
        risks.append("Down payment data unavailable")

    return {
        "score": score,
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": "Down payment assessment.",
    }


def _score_employment_history(application: Application, **kwargs) -> dict[str, Any]:
    emp = application.employment_info or {}
    score, positive, risks, mitigating = 50.0, [], [], []

    if emp.get("employer_name") and emp.get("job_title"):
        score += 10
        positive.append("Complete employment info")
    if emp.get("employment_status") == "employed" and emp.get("years_at_job", 0) >= 2:
        score += 25
        positive.append("Stable employment")
    if emp.get("previous_employer"):
        score += 10
        positive.append("History documented")

    return {
        "score": min(score, 100),
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": "Employment history assessment.",
    }


def _score_property_assessment(application: Application, **kwargs) -> dict[str, Any]:
    prop = application.property_info or {}
    score, positive, risks, mitigating = 50.0, [], [], []

    ptype = prop.get("property_type", "")
    if ptype in ("single_family", "townhouse"):
        score += 20
        positive.append(f"Standard type ({ptype.replace('_', ' ')})")
    elif ptype == "condo":
        score += 15
        positive.append("Condominium")

    usage = prop.get("usage_type", "")
    if usage == "primary_residence":
        score += 20
        positive.append("Primary residence")
    elif usage == "investment":
        risks.append("Investment property")

    if prop.get("purchase_price", 0) >= 100000:
        score += 10
        positive.append("Property value supports collateral")

    return {
        "score": min(score, 100),
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": "Property assessment.",
    }


def _score_fraud_risk(
    application: Application, credit_report_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score fraud risk based on credit bureau fraud indicators."""
    score = 90.0  # Start high (low risk = good)
    positive, risks, mitigating = [], [], []

    if not credit_report_data:
        return {
            "score": 70.0,
            "positive_factors": ["No fraud indicators without bureau data"],
            "risk_factors": risks,
            "mitigating_factors": mitigating,
            "explanation": "Fraud risk could not be fully evaluated without bureau data.",
        }

    fraud_score = credit_report_data.get("fraud_score", 0)
    fraud_alerts = credit_report_data.get("fraud_alerts", [])
    inquiries = credit_report_data.get("inquiries", [])
    utilization = credit_report_data.get("credit_utilization", 0)

    # Fraud score impact (inverted: high fraud_score = low risk score)
    if fraud_score >= 60:
        score = 15.0
        risks.append(f"High fraud risk score ({fraud_score}/100)")
    elif fraud_score >= 40:
        score = 45.0
        risks.append(f"Elevated fraud risk score ({fraud_score}/100)")
    elif fraud_score >= 20:
        score = 70.0
        risks.append(f"Minor fraud indicators ({fraud_score}/100)")
    else:
        positive.append(f"Low fraud risk ({fraud_score}/100)")

    # Process fraud alerts
    high_alerts = [a for a in fraud_alerts if isinstance(a, dict) and a.get("severity") == "high"]
    if high_alerts:
        score -= len(high_alerts) * 15
        for alert in high_alerts:
            risks.append(f"[HIGH] {alert.get('description', 'High severity fraud alert')}")

    # Debt velocity check
    if utilization > 70:
        score -= 10
        risks.append(f"High utilization ({utilization:.0f}%) indicates potential debt accumulation")

    recent_inquiries = len([
        i for i in inquiries
        if isinstance(i, dict) and i.get("inquiry_type") != "mortgage"
    ])
    if recent_inquiries > 3:
        score -= 10
        risks.append(
            f"{recent_inquiries} non-mortgage inquiries — possible credit seeking behavior"
        )

    if not risks:
        positive.append("No fraud indicators detected")

    return {
        "score": max(0, min(100, score)),
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": f"Fraud risk assessment: bureau fraud score {fraud_score}/100.",
    }


def _score_compensating_factors(
    application: Application, credit_report_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score compensating factors that can offset weaknesses elsewhere."""
    score = 50.0
    positive, risks, mitigating = [], [], []

    financial = application.financial_info or {}
    employment = application.employment_info or {}
    declarations = application.declarations or {}
    dp = float(application.down_payment) if application.down_payment else 0
    pp = (application.property_info or {}).get("purchase_price", 0)
    dp_pct = (dp / pp * 100) if pp and dp else 0

    annual_income = employment.get("annual_income", 0) or 0
    years_at_job = employment.get("years_at_job", 0) or 0
    liquid_assets = financial.get("liquid_assets", 0) or 0
    dti = float(application.dti_ratio) if application.dti_ratio else None
    loan_amount = float(application.loan_amount) if application.loan_amount else 0

    # Down payment >= 25% → significant skin in the game
    if dp_pct >= 25:
        score += 10
        positive.append(f"Large down payment ({dp_pct:.1f}%) demonstrates commitment")
    elif dp_pct >= 20:
        score += 6
        positive.append(f"Standard 20%+ down payment ({dp_pct:.1f}%)")

    # Liquid reserves check
    # Estimate monthly mortgage payment
    monthly_payment = 0
    if loan_amount > 0:
        rate = 6.5 / 100 / 12  # Default estimate
        term = 360
        if rate > 0:
            monthly_payment = loan_amount * (
                rate * (1 + rate) ** term
            ) / ((1 + rate) ** term - 1)

    reserves_after_dp = max(0, liquid_assets - dp)
    months_of_reserves = (
        reserves_after_dp / monthly_payment if monthly_payment > 0 else 0
    )

    if months_of_reserves >= 12:
        score += 10
        positive.append(
            f"Excellent reserves ({months_of_reserves:.0f} months of payments after down payment)"
        )
    elif months_of_reserves >= 6:
        score += 6
        positive.append(f"Good reserves ({months_of_reserves:.0f} months)")
    elif months_of_reserves >= 3:
        score += 2
    elif monthly_payment > 0:
        score -= 10
        risks.append(
            f"Thin reserves ({months_of_reserves:.1f} months) — "
            "less than 3 months of mortgage payments after down payment"
        )

    # Annual income >= 3x annual mortgage obligation
    annual_mortgage = monthly_payment * 12
    if annual_income > 0 and annual_mortgage > 0:
        income_to_mortgage = annual_income / annual_mortgage
        if income_to_mortgage >= 3:
            score += 8
            positive.append(
                f"Income covers {income_to_mortgage:.1f}x annual mortgage obligation"
            )

    # Low DTI despite other concerns
    if dti is not None and dti <= 28:
        score += 6
        positive.append(f"Conservative DTI ({dti:.1f}%) provides payment cushion")

    # Long employment tenure
    if years_at_job >= 5:
        score += 5
        positive.append(f"Employment stability ({years_at_job} years at current employer)")

    # Recovery trajectory detection
    has_derogatory = (
        declarations.get("has_bankruptcy")
        or declarations.get("has_foreclosure")
    )
    if has_derogatory and credit_report_data:
        # Check if recent payment history is clean
        tradelines = credit_report_data.get("tradelines", [])
        recent_all_clean = True
        for t in tradelines:
            if isinstance(t, dict):
                history = t.get("payment_history_24m", [])
                recent_24 = history[:24]
                if any(p != "OK" for p in recent_24):
                    recent_all_clean = False
                    break

        if recent_all_clean and tradelines:
            score += 12
            positive.append(
                "Recovery trajectory: past derogatory marks with "
                "24 months of clean payment history"
            )

    # Stress test
    if annual_income > 0 and loan_amount > 0:
        stressed_monthly_income = (annual_income * 0.80) / 12
        stressed_rate = 8.5 / 100 / 12  # ~6.5% + 2%
        term = 360
        if stressed_rate > 0:
            stressed_payment = loan_amount * (
                stressed_rate * (1 + stressed_rate) ** term
            ) / ((1 + stressed_rate) ** term - 1)
            monthly_debts = financial.get("monthly_debts", {})
            total_debts = sum(
                float(v) for v in monthly_debts.values()
                if isinstance(v, (int, float))
            )
            stressed_dti = (
                (stressed_payment + total_debts) / stressed_monthly_income * 100
            )
            if stressed_dti <= 43:
                score += 8
                positive.append(
                    f"Passes stress test: DTI {stressed_dti:.1f}% under "
                    "20% income reduction + 2% rate increase"
                )
            elif stressed_dti > 50:
                score -= 8
                risks.append(
                    f"Fails stress test: DTI would reach {stressed_dti:.1f}% under "
                    "adverse conditions (20% income drop + 2% rate increase)"
                )

    return {
        "score": max(0, min(100, score)),
        "positive_factors": positive,
        "risk_factors": risks,
        "mitigating_factors": mitigating,
        "explanation": "Compensating factors assessment.",
    }


DIMENSION_SCORERS = {
    "credit_profile": _score_credit_profile,
    "credit_history_depth": _score_credit_history_depth,
    "payment_history": _score_payment_history,
    "income_stability": _score_income_stability,
    "earning_potential": _score_earning_potential,
    "debt_to_income": _score_debt_to_income,
    "down_payment": _score_down_payment,
    "employment_history": _score_employment_history,
    "property_assessment": _score_property_assessment,
    "fraud_risk": _score_fraud_risk,
    "compensating_factors": _score_compensating_factors,
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
    rule-based scoring otherwise. Pulls a credit bureau report before
    running dimension agents.

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

        # --- Credit Bureau Pull ---
        credit_report_data = None
        try:
            report = CreditBureauService.pull_credit_report(
                application_id=application_id,
                financial_info=application.financial_info or {},
                employment_info=application.employment_info or {},
                declarations=application.declarations or {},
                property_info=application.property_info or {},
            )
            credit_report_data = report.to_dict()

            # Persist credit report to database
            cr_record = CreditReport(
                application_id=application.id,
                credit_score=report.credit_score,
                score_model=report.score_model,
                score_factors=report.score_factors,
                tradelines=[
                    t if isinstance(t, dict) else t.__dict__
                    for t in report.tradelines
                ],
                public_records=[
                    r if isinstance(r, dict) else r.__dict__
                    for r in report.public_records
                ],
                inquiries=[
                    i if isinstance(i, dict) else i.__dict__
                    for i in report.inquiries
                ],
                collections=report.collections,
                total_accounts=report.total_accounts,
                open_accounts=report.open_accounts,
                credit_utilization=Decimal(str(report.credit_utilization)),
                oldest_account_months=report.oldest_account_months,
                avg_account_age_months=report.avg_account_age_months,
                on_time_payments_pct=Decimal(str(report.on_time_payments_pct)),
                late_payments_30d=report.late_payments_30d,
                late_payments_60d=report.late_payments_60d,
                late_payments_90d=report.late_payments_90d,
                fraud_alerts=[
                    a if isinstance(a, dict) else a.__dict__
                    for a in report.fraud_alerts
                ],
                fraud_score=report.fraud_score,
            )
            session.add(cr_record)
            session.commit()
            logger.info(
                f"Credit report stored for application {application_id}: "
                f"score={report.credit_score}, fraud={report.fraud_score}"
            )
        except Exception as exc:
            logger.warning(
                f"Credit bureau pull failed for {application_id}: {exc}. "
                "Continuing without bureau data."
            )

        # Build application data for the pipeline
        app_data = ApplicationData.from_orm(application)
        app_data.credit_report = credit_report_data

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
            assessment.llm_model = "v2.0"

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
