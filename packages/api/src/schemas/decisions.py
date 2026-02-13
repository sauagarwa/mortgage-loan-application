"""
Decision and risk assessment Pydantic schemas.
"""

from datetime import datetime

from pydantic import BaseModel


class RiskDimensionScoreResponse(BaseModel):
    """Individual risk dimension score."""

    name: str
    score: float
    weight: float
    weighted_score: float
    agent: str
    positive_factors: list[str] = []
    risk_factors: list[str] = []
    mitigating_factors: list[str] = []
    explanation: str | None = None


class RiskCondition(BaseModel):
    """A condition for conditional approval."""

    condition: str
    status: str = "pending"


class RiskAssessmentResponse(BaseModel):
    """Full risk assessment response (servicer view)."""

    id: str
    application_id: str
    status: str
    overall_score: float | None = None
    risk_band: str | None = None
    confidence: float | None = None
    recommendation: str | None = None
    summary: str | None = None
    dimensions: list[RiskDimensionScoreResponse] = []
    conditions: list[RiskCondition] = []
    processing_metadata: dict | None = None


class RiskAssessmentApplicantView(BaseModel):
    """Simplified risk assessment response (applicant view)."""

    id: str
    status: str
    overall_score: float | None = None
    risk_band: str | None = None
    recommendation: str | None = None
    summary: str | None = None
    positive_highlights: list[str] = []
    areas_of_concern: list[str] = []


class DecisionCreate(BaseModel):
    """Request to create a loan decision."""

    decision: str  # approved, denied, conditionally_approved
    conditions: list[str] = []
    adverse_action_reasons: list[str] = []
    interest_rate: float | None = None
    approved_loan_amount: float | None = None
    approved_term_years: int | None = None
    notes: str | None = None
    override_ai_recommendation: bool = False
    override_justification: str | None = None


class DecisionResponse(BaseModel):
    """Decision response."""

    id: str
    application_id: str
    decision: str
    ai_recommendation: str | None = None
    servicer_agreed_with_ai: bool | None = None
    override_justification: str | None = None
    conditions: list[str] = []
    adverse_action_reasons: list[str] = []
    interest_rate: float | None = None
    approved_loan_amount: float | None = None
    approved_term_years: int | None = None
    monthly_payment: float | None = None
    notes: str | None = None
    explanation: str | None = None
    decided_by_name: str | None = None
    decided_by_role: str | None = None
    decided_at: datetime | None = None


class InfoRequestItem(BaseModel):
    """Single item in an information request."""

    type: str  # document, clarification
    document_type: str | None = None
    description: str | None = None
    question: str | None = None


class InfoRequestCreate(BaseModel):
    """Request additional information from applicant."""

    requested_items: list[InfoRequestItem]
    due_date: str | None = None


class InfoRequestResponse(BaseModel):
    """Response after creating an info request."""

    application_id: str
    status: str
    requested_items: list[InfoRequestItem]
    due_date: str | None = None
    message: str
