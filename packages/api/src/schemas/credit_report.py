"""
Pydantic schemas for credit report responses.
"""

from pydantic import BaseModel


class TradelineResponse(BaseModel):
    """Individual tradeline in the credit report."""

    account_type: str
    creditor: str
    opened_date: str
    credit_limit: float | None = None
    current_balance: float = 0
    monthly_payment: float = 0
    status: str = "open"
    payment_history_24m: list[str] = []


class PublicRecordResponse(BaseModel):
    """Public record entry."""

    record_type: str
    filed_date: str
    status: str
    amount: float | None = None


class InquiryResponse(BaseModel):
    """Credit inquiry."""

    date: str
    creditor: str
    inquiry_type: str


class FraudAlertResponse(BaseModel):
    """Fraud alert indicator."""

    alert_type: str
    severity: str
    description: str


class CollectionResponse(BaseModel):
    """Collection account."""

    agency: str
    original_creditor: str
    amount: float
    status: str
    reported_date: str


class CreditReportResponse(BaseModel):
    """Full credit report response."""

    id: str
    application_id: str

    # Credit score
    credit_score: int
    score_model: str
    score_factors: list[str] = []

    # Tradelines and records
    tradelines: list[TradelineResponse] = []
    public_records: list[PublicRecordResponse] = []
    inquiries: list[InquiryResponse] = []
    collections: list[CollectionResponse] = []

    # Fraud indicators
    fraud_alerts: list[FraudAlertResponse] = []
    fraud_score: int = 0

    # Summary metrics
    total_accounts: int = 0
    open_accounts: int = 0
    credit_utilization: float | None = None
    oldest_account_months: int | None = None
    avg_account_age_months: int | None = None

    # Payment history
    on_time_payments_pct: float | None = None
    late_payments_30d: int = 0
    late_payments_60d: int = 0
    late_payments_90d: int = 0

    # Metadata
    pulled_at: str | None = None
