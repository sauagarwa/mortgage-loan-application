"""
SQLAdmin configuration for database administration UI

Access the admin panel at: http://localhost:8000/admin
"""

from db import Application, AuditLog, Decision, Document, LLMConfig, LoanProduct, User
from sqladmin import Admin, ModelView
from sqlalchemy import create_engine

from .core.config import settings

engine = create_engine(settings.database_url_sync, echo=False)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.first_name, User.last_name, User.role, User.is_active]
    column_searchable_list = [User.email, User.first_name, User.last_name]
    column_sortable_list = [User.email, User.role, User.created_at]
    column_default_sort = [(User.created_at, True)]
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"


class LoanProductAdmin(ModelView, model=LoanProduct):
    column_list = [
        LoanProduct.id,
        LoanProduct.name,
        LoanProduct.type,
        LoanProduct.term_years,
        LoanProduct.rate_type,
        LoanProduct.is_active,
    ]
    column_searchable_list = [LoanProduct.name, LoanProduct.type]
    column_sortable_list = [LoanProduct.name, LoanProduct.type, LoanProduct.term_years]
    name = "Loan Product"
    name_plural = "Loan Products"
    icon = "fa-solid fa-landmark"


class ApplicationAdmin(ModelView, model=Application):
    column_list = [
        Application.id,
        Application.application_number,
        Application.status,
        Application.loan_amount,
        Application.created_at,
    ]
    column_searchable_list = [Application.application_number, Application.status]
    column_sortable_list = [
        Application.application_number,
        Application.status,
        Application.created_at,
    ]
    column_default_sort = [(Application.created_at, True)]
    name = "Application"
    name_plural = "Applications"
    icon = "fa-solid fa-file-lines"


class DocumentAdmin(ModelView, model=Document):
    column_list = [
        Document.id,
        Document.document_type,
        Document.original_filename,
        Document.status,
        Document.uploaded_at,
    ]
    column_sortable_list = [Document.document_type, Document.status, Document.uploaded_at]
    name = "Document"
    name_plural = "Documents"
    icon = "fa-solid fa-file-pdf"


class DecisionAdmin(ModelView, model=Decision):
    column_list = [
        Decision.id,
        Decision.decision,
        Decision.ai_recommendation,
        Decision.servicer_agreed_with_ai,
        Decision.decided_at,
    ]
    column_sortable_list = [Decision.decision, Decision.decided_at]
    name = "Decision"
    name_plural = "Decisions"
    icon = "fa-solid fa-gavel"


class LLMConfigAdmin(ModelView, model=LLMConfig):
    column_list = [
        LLMConfig.id,
        LLMConfig.provider,
        LLMConfig.is_active,
        LLMConfig.is_default,
        LLMConfig.default_model,
    ]
    name = "LLM Config"
    name_plural = "LLM Configs"
    icon = "fa-solid fa-robot"


class AuditLogAdmin(ModelView, model=AuditLog):
    column_list = [
        AuditLog.id,
        AuditLog.timestamp,
        AuditLog.user_email,
        AuditLog.action,
        AuditLog.resource_type,
    ]
    column_sortable_list = [AuditLog.timestamp, AuditLog.action]
    column_default_sort = [(AuditLog.timestamp, True)]
    can_create = False
    can_edit = False
    can_delete = False
    name = "Audit Log"
    name_plural = "Audit Logs"
    icon = "fa-solid fa-clipboard-list"


def setup_admin(app):
    """Set up SQLAdmin and mount it to the FastAPI app."""
    admin = Admin(app, engine, title="MortgageAI Admin")

    admin.add_view(UserAdmin)
    admin.add_view(LoanProductAdmin)
    admin.add_view(ApplicationAdmin)
    admin.add_view(DocumentAdmin)
    admin.add_view(DecisionAdmin)
    admin.add_view(LLMConfigAdmin)
    admin.add_view(AuditLogAdmin)

    return admin
