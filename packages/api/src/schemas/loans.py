"""
Loan product Pydantic schemas.
"""

from pydantic import BaseModel, Field


class LoanProductResponse(BaseModel):
    """Loan product response."""

    id: str
    name: str
    type: str
    term_years: int
    rate_type: str
    min_down_payment_pct: float
    min_credit_score: int | None = None
    max_dti_ratio: float | None = None
    max_loan_amount: float | None = None
    description: str | None = None
    eligibility_requirements: list[str] = []
    features: list[str] = []
    is_active: bool = True


class LoanProductListResponse(BaseModel):
    """Paginated list of loan products."""

    items: list[LoanProductResponse]
    total: int


class EligibilityCheckRequest(BaseModel):
    """Pre-qualification eligibility check request."""

    annual_income: float = Field(gt=0)
    monthly_debts: float = Field(ge=0)
    credit_score_range: str = Field(
        description="Self-reported credit score range, e.g. '620-679'"
    )
    down_payment_amount: float = Field(ge=0)
    property_value: float = Field(gt=0)
    citizenship_status: str = Field(
        description="citizen, permanent_resident, visa_holder, non_resident"
    )


class EligibilityCheckResponse(BaseModel):
    """Pre-qualification eligibility check result."""

    eligible: bool
    estimated_rate: str | None = None
    estimated_monthly_payment: float | None = None
    max_loan_amount: float | None = None
    warnings: list[str] = []
    suggestions: list[str] = []
