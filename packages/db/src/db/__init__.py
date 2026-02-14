__version__ = "0.1.0"

# Export main database classes and functions
from .database import Base, DatabaseService, get_db, get_db_service
from .models import (
    Application,
    AuditLog,
    CreditReport,
    Decision,
    Document,
    InfoRequest,
    LLMConfig,
    LoanProduct,
    Notification,
    RiskAssessment,
    RiskDimensionScore,
    User,
)

__all__ = [
    "DatabaseService",
    "get_db_service",
    "get_db",
    "Base",
    "User",
    "LoanProduct",
    "Application",
    "Document",
    "RiskAssessment",
    "RiskDimensionScore",
    "CreditReport",
    "Decision",
    "InfoRequest",
    "LLMConfig",
    "AuditLog",
    "Notification",
    "__version__",
]
