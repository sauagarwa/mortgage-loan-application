"""
MortgageAI database models

All SQLAlchemy ORM models for the mortgage loan origination platform.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


def generate_uuid():
    return uuid.uuid4()


class User(Base):
    """User accounts synced from Keycloak."""

    __tablename__ = "user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String(50), nullable=False, default="applicant", index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    applications = relationship(
        "Application", back_populates="applicant", foreign_keys="Application.applicant_id"
    )
    serviced_applications = relationship(
        "Application",
        back_populates="assigned_servicer",
        foreign_keys="Application.assigned_servicer_id",
    )
    decisions = relationship("Decision", back_populates="decided_by_user")
    notifications = relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class LoanProduct(Base):
    """Catalog of available mortgage loan products."""

    __tablename__ = "loan_product"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    term_years = Column(Integer, nullable=False)
    rate_type = Column(String(20), nullable=False)
    min_down_payment_pct = Column(Numeric(5, 2), nullable=False)
    min_credit_score = Column(Integer, nullable=True)
    max_dti_ratio = Column(Numeric(5, 2), nullable=True)
    max_loan_amount = Column(Numeric(15, 2), nullable=True)
    description = Column(Text, nullable=True)
    eligibility_requirements = Column(JSONB, nullable=False, server_default="[]")
    features = Column(JSONB, nullable=False, server_default="[]")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    applications = relationship("Application", back_populates="loan_product")

    def __repr__(self):
        return f"<LoanProduct(id={self.id}, name='{self.name}', type='{self.type}')>"


class Application(Base):
    """Mortgage loan application."""

    __tablename__ = "application"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    application_number = Column(String(20), unique=True, nullable=False, index=True)
    applicant_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    loan_product_id = Column(
        UUID(as_uuid=True), ForeignKey("loan_product.id"), nullable=False, index=True
    )
    assigned_servicer_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True
    )
    status = Column(String(50), nullable=False, default="draft", index=True)

    # JSONB fields for flexible structured data
    personal_info = Column(JSONB, nullable=False, server_default="{}")
    employment_info = Column(JSONB, nullable=False, server_default="{}")
    financial_info = Column(JSONB, nullable=False, server_default="{}")
    property_info = Column(JSONB, nullable=False, server_default="{}")
    declarations = Column(JSONB, nullable=False, server_default="{}")

    # Computed fields
    loan_amount = Column(Numeric(15, 2), nullable=True)
    down_payment = Column(Numeric(15, 2), nullable=True)
    dti_ratio = Column(Numeric(5, 2), nullable=True)

    # Timestamps
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    applicant = relationship("User", back_populates="applications", foreign_keys=[applicant_id])
    assigned_servicer = relationship(
        "User", back_populates="serviced_applications", foreign_keys=[assigned_servicer_id]
    )
    loan_product = relationship("LoanProduct", back_populates="applications")
    documents = relationship(
        "Document", back_populates="application", cascade="all, delete-orphan"
    )
    risk_assessments = relationship("RiskAssessment", back_populates="application")
    credit_reports = relationship(
        "CreditReport", back_populates="application", cascade="all, delete-orphan"
    )
    decision = relationship("Decision", back_populates="application", uselist=False)
    info_requests = relationship("InfoRequest", back_populates="application")
    notifications = relationship("Notification", back_populates="application")

    __table_args__ = (
        Index("idx_application_applicant_status", "applicant_id", "status"),
        Index("idx_application_servicer_status", "assigned_servicer_id", "status"),
    )

    def __repr__(self):
        return (
            f"<Application(id={self.id}, number='{self.application_number}', "
            f"status='{self.status}')>"
        )


class Document(Base):
    """Uploaded documents and their OCR-extracted data."""

    __tablename__ = "document"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type = Column(String(50), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_key = Column(String(500), nullable=False)
    status = Column(String(30), nullable=False, default="uploaded", index=True)
    extracted_data = Column(JSONB, nullable=True)
    extraction_confidence = Column(Numeric(3, 2), nullable=True)
    processing_error = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    application = relationship("Application", back_populates="documents")

    __table_args__ = (
        Index("idx_document_application_type", "application_id", "document_type"),
    )

    def __repr__(self):
        return (
            f"<Document(id={self.id}, type='{self.document_type}', "
            f"status='{self.status}')>"
        )


class RiskAssessment(Base):
    """Top-level risk assessment results for an application."""

    __tablename__ = "risk_assessment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.id"), nullable=False, index=True
    )
    status = Column(String(30), nullable=False, default="pending", index=True)
    overall_score = Column(Numeric(5, 2), nullable=True)
    risk_band = Column(String(20), nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    recommendation = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    conditions = Column(JSONB, server_default="[]")
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)
    total_tokens = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    application = relationship("Application", back_populates="risk_assessments")
    dimension_scores = relationship(
        "RiskDimensionScore",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
    )
    decision = relationship("Decision", back_populates="risk_assessment")

    def __repr__(self):
        return (
            f"<RiskAssessment(id={self.id}, score={self.overall_score}, "
            f"band='{self.risk_band}')>"
        )


class RiskDimensionScore(Base):
    """Individual dimension scores from each MCP agent."""

    __tablename__ = "risk_dimension_score"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    risk_assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("risk_assessment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dimension_name = Column(String(100), nullable=False)
    agent_name = Column(String(100), nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=False)
    weight = Column(Numeric(3, 2), nullable=False)
    weighted_score = Column(Numeric(5, 2), nullable=False)
    positive_factors = Column(JSONB, nullable=False, server_default="[]")
    risk_factors = Column(JSONB, nullable=False, server_default="[]")
    mitigating_factors = Column(JSONB, nullable=False, server_default="[]")
    explanation = Column(Text, nullable=True)
    raw_agent_output = Column(JSONB, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    risk_assessment = relationship("RiskAssessment", back_populates="dimension_scores")

    def __repr__(self):
        return (
            f"<RiskDimensionScore(dimension='{self.dimension_name}', "
            f"score={self.score}, agent='{self.agent_name}')>"
        )


class Decision(Base):
    """Final loan decision made by the servicer."""

    __tablename__ = "decision"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.id"), unique=True, nullable=False, index=True
    )
    risk_assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("risk_assessment.id"), nullable=True
    )
    decided_by = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    decision = Column(String(30), nullable=False, index=True)
    ai_recommendation = Column(String(50), nullable=True)
    servicer_agreed_with_ai = Column(Boolean, nullable=True)
    override_justification = Column(Text, nullable=True)
    conditions = Column(JSONB, server_default="[]")
    adverse_action_reasons = Column(JSONB, server_default="[]")
    interest_rate = Column(Numeric(5, 3), nullable=True)
    approved_loan_amount = Column(Numeric(15, 2), nullable=True)
    approved_term_years = Column(Integer, nullable=True)
    monthly_payment = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    application = relationship("Application", back_populates="decision")
    risk_assessment = relationship("RiskAssessment", back_populates="decision")
    decided_by_user = relationship("User", back_populates="decisions")

    __table_args__ = (Index("idx_decision_date", "decided_at"),)

    def __repr__(self):
        return f"<Decision(id={self.id}, decision='{self.decision}')>"


class InfoRequest(Base):
    """Additional information requests from servicers."""

    __tablename__ = "info_request"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.id"), nullable=False, index=True
    )
    requested_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    requested_items = Column(JSONB, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="pending", index=True)
    response_notes = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    application = relationship("Application", back_populates="info_requests")
    requested_by_user = relationship("User")

    def __repr__(self):
        return f"<InfoRequest(id={self.id}, status='{self.status}')>"


class LLMConfig(Base):
    """LLM provider configuration."""

    __tablename__ = "llm_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    provider = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    is_default = Column(Boolean, nullable=False, default=False)
    base_url = Column(String(500), nullable=False)
    api_key_encrypted = Column(String(500), nullable=True)
    default_model = Column(String(100), nullable=False)
    max_tokens = Column(Integer, nullable=False, default=4096)
    temperature = Column(Numeric(3, 2), nullable=False, default=0.10)
    rate_limit_rpm = Column(Integer, nullable=True, default=60)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return (
            f"<LLMConfig(provider='{self.provider}', active={self.is_active}, "
            f"default={self.is_default})>"
        )


class CreditReport(Base):
    """Simulated credit bureau report for an application."""

    __tablename__ = "credit_report"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Credit score
    credit_score = Column(Integer, nullable=False)
    score_model = Column(String(50), nullable=False, default="FICO 8")
    score_factors = Column(JSONB, nullable=False, server_default="[]")

    # Tradeline and account data (JSONB arrays)
    tradelines = Column(JSONB, nullable=False, server_default="[]")
    public_records = Column(JSONB, nullable=False, server_default="[]")
    inquiries = Column(JSONB, nullable=False, server_default="[]")
    collections = Column(JSONB, nullable=False, server_default="[]")

    # Summary metrics
    total_accounts = Column(Integer, nullable=False, default=0)
    open_accounts = Column(Integer, nullable=False, default=0)
    credit_utilization = Column(Numeric(5, 2), nullable=True)
    oldest_account_months = Column(Integer, nullable=True)
    avg_account_age_months = Column(Integer, nullable=True)

    # Payment history
    on_time_payments_pct = Column(Numeric(5, 2), nullable=True)
    late_payments_30d = Column(Integer, nullable=False, default=0)
    late_payments_60d = Column(Integer, nullable=False, default=0)
    late_payments_90d = Column(Integer, nullable=False, default=0)

    # Fraud indicators
    fraud_alerts = Column(JSONB, nullable=False, server_default="[]")
    fraud_score = Column(Integer, nullable=False, default=0)

    # Timestamps
    pulled_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    application = relationship("Application", back_populates="credit_reports")

    def __repr__(self):
        return (
            f"<CreditReport(id={self.id}, score={self.credit_score}, "
            f"fraud_score={self.fraud_score})>"
        )


class AuditLog(Base):
    """Immutable audit trail for all significant actions."""

    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    timestamp = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
    )

    def __repr__(self):
        return (
            f"<AuditLog(action='{self.action}', resource='{self.resource_type}', "
            f"user='{self.user_email}')>"
        )


class Notification(Base):
    """User notifications."""

    __tablename__ = "notification"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.id"), nullable=True
    )
    is_read = Column(Boolean, nullable=False, default=False)
    email_sent = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")
    application = relationship("Application", back_populates="notifications")

    __table_args__ = (
        Index("idx_notification_unread", "user_id", "is_read"),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.type}', read={self.is_read})>"
