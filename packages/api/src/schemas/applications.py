"""
Application Pydantic schemas.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class AddressSchema(BaseModel):
    """Address sub-schema."""

    street: str
    city: str
    state: str
    zip_code: str


class PersonalInfoSchema(BaseModel):
    """Personal information section of the application."""

    first_name: str
    last_name: str
    date_of_birth: str | None = None
    ssn_last_four: str | None = None
    email: str
    phone: str | None = None
    address: AddressSchema | None = None
    citizenship_status: str | None = None
    visa_type: str | None = None
    years_in_country: int | None = None


class EmploymentInfoSchema(BaseModel):
    """Employment information section."""

    employment_status: str | None = None
    employer_name: str | None = None
    job_title: str | None = None
    years_at_current_job: float | None = None
    years_in_field: float | None = None
    annual_income: float | None = None
    additional_income: float | None = None
    additional_income_source: str | None = None
    is_self_employed: bool = False


class MonthlyDebtsSchema(BaseModel):
    """Monthly debts breakdown."""

    car_loan: float = 0
    student_loans: float = 0
    credit_cards: float = 0
    other: float = 0


class FinancialInfoSchema(BaseModel):
    """Financial information section."""

    credit_score_self_reported: int | None = None
    has_credit_history: bool | None = None
    monthly_debts: MonthlyDebtsSchema | None = None
    total_assets: float | None = None
    liquid_assets: float | None = None
    checking_balance: float | None = None
    savings_balance: float | None = None
    retirement_accounts: float | None = None
    investment_accounts: float | None = None
    bankruptcy_history: bool = False
    foreclosure_history: bool = False


class PropertyInfoSchema(BaseModel):
    """Property information section."""

    property_type: str | None = None
    property_use: str | None = None
    purchase_price: float | None = None
    down_payment: float | None = None
    address: AddressSchema | None = None


class DeclarationsSchema(BaseModel):
    """Applicant declarations."""

    outstanding_judgments: bool = False
    party_to_lawsuit: bool = False
    federal_debt_delinquent: bool = False
    alimony_obligation: bool = False
    co_signer_on_other_loan: bool = False
    us_citizen: bool = True
    primary_residence: bool = True


class ApplicationCreate(BaseModel):
    """Create a new mortgage application."""

    loan_product_id: str
    personal_info: PersonalInfoSchema | None = None
    employment_info: EmploymentInfoSchema | None = None
    financial_info: FinancialInfoSchema | None = None
    property_info: PropertyInfoSchema | None = None
    declarations: DeclarationsSchema | None = None


class ApplicationUpdate(BaseModel):
    """Update a draft application (partial updates allowed)."""

    loan_product_id: str | None = None
    personal_info: PersonalInfoSchema | None = None
    employment_info: EmploymentInfoSchema | None = None
    financial_info: FinancialInfoSchema | None = None
    property_info: PropertyInfoSchema | None = None
    declarations: DeclarationsSchema | None = None


class DocumentSummary(BaseModel):
    """Brief document info for embedding in application response."""

    id: str
    document_type: str
    filename: str
    status: str
    uploaded_at: datetime | None = None


class RiskAssessmentSummary(BaseModel):
    """Brief risk assessment info for embedding in application response."""

    id: str
    status: str
    overall_score: float | None = None
    risk_band: str | None = None
    recommendation: str | None = None


class DecisionSummary(BaseModel):
    """Brief decision info for embedding in application response."""

    id: str
    decision: str
    decided_at: datetime | None = None


class ApplicationResponse(BaseModel):
    """Full application response."""

    id: str
    application_number: str
    status: str
    loan_product_id: str
    loan_product_name: str | None = None
    loan_product_type: str | None = None
    applicant_id: str
    applicant_name: str | None = None
    assigned_servicer_id: str | None = None
    assigned_servicer_name: str | None = None
    personal_info: dict = {}
    employment_info: dict = {}
    financial_info: dict = {}
    property_info: dict = {}
    declarations: dict = {}
    loan_amount: float | None = None
    down_payment: float | None = None
    dti_ratio: float | None = None
    documents: list[DocumentSummary] = []
    risk_assessment: RiskAssessmentSummary | None = None
    decision: DecisionSummary | None = None
    submitted_at: datetime | None = None
    decided_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApplicationListItem(BaseModel):
    """Lightweight application item for list views."""

    id: str
    application_number: str
    status: str
    applicant_name: str | None = None
    loan_type: str | None = None
    loan_amount: float | None = None
    risk_score: float | None = None
    risk_band: str | None = None
    submitted_at: datetime | None = None
    created_at: datetime | None = None
    assigned_servicer: str | None = None


class PaginatedApplications(BaseModel):
    """Paginated list of applications."""

    items: list[ApplicationListItem]
    total: int
    limit: int
    offset: int


class ApplicationSubmitResponse(BaseModel):
    """Response after submitting an application."""

    id: str
    status: str
    submitted_at: datetime
    message: str


class ApplicationAssignRequest(BaseModel):
    """Request to assign a servicer to an application."""

    servicer_id: str = Field(description="UUID of the servicer to assign")
