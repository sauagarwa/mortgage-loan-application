"""
Application routes - CRUD operations for mortgage applications.
"""

import random
import string
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import Application, Document, LoanProduct, RiskAssessment, User, get_db

from ..core.security import TokenUser, get_current_user, require_role
from ..services.websocket_manager import publish_event
from ..worker.tasks.document_processing import process_application_documents
from ..worker.tasks.risk_assessment import run_risk_assessment
from ..schemas.applications import (
    ApplicationAssignRequest,
    ApplicationCreate,
    ApplicationListItem,
    ApplicationResponse,
    ApplicationSubmitResponse,
    ApplicationUpdate,
    DecisionSummary,
    DocumentSummary,
    PaginatedApplications,
    RiskAssessmentSummary,
)

router = APIRouter()


def _generate_application_number() -> str:
    """Generate a unique application number like MA-2026-XXXXX."""
    year = datetime.now(UTC).year
    suffix = "".join(random.choices(string.digits, k=5))
    return f"MA-{year}-{suffix}"


async def _get_or_create_user(
    token_user: TokenUser, session: AsyncSession
) -> User:
    """Get the local user record, creating if needed."""
    result = await session.execute(
        select(User).where(User.keycloak_id == token_user.keycloak_id)
    )
    db_user = result.scalar_one_or_none()
    if db_user is None:
        db_user = User(
            keycloak_id=token_user.keycloak_id,
            email=token_user.email,
            first_name=token_user.first_name,
            last_name=token_user.last_name,
            role=token_user.primary_role,
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
    return db_user


async def _get_application_with_access(
    application_id: UUID,
    user: TokenUser,
    session: AsyncSession,
    require_owner: bool = False,
) -> Application:
    """Get an application with access control checks."""
    result = await session.execute(
        select(Application)
        .options(
            selectinload(Application.loan_product),
            selectinload(Application.applicant),
            selectinload(Application.assigned_servicer),
            selectinload(Application.documents),
            selectinload(Application.risk_assessments),
            selectinload(Application.decision),
        )
        .where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()

    if app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Access control
    if user.is_applicant and not user.is_loan_servicer and not user.is_admin:
        db_user = await _get_or_create_user(user, session)
        if app.applicant_id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this application",
            )

    if require_owner:
        db_user = await _get_or_create_user(user, session)
        if app.applicant_id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the applicant can perform this action",
            )

    return app


def _build_application_response(app: Application) -> ApplicationResponse:
    """Build a full application response from the ORM model."""
    # Get latest risk assessment
    risk_summary = None
    if app.risk_assessments:
        latest_ra = sorted(
            app.risk_assessments, key=lambda r: r.created_at, reverse=True
        )[0]
        risk_summary = RiskAssessmentSummary(
            id=str(latest_ra.id),
            status=latest_ra.status,
            overall_score=float(latest_ra.overall_score) if latest_ra.overall_score else None,
            risk_band=latest_ra.risk_band,
            recommendation=latest_ra.recommendation,
        )

    # Decision summary
    decision_summary = None
    if app.decision:
        decision_summary = DecisionSummary(
            id=str(app.decision.id),
            decision=app.decision.decision,
            decided_at=app.decision.decided_at,
        )

    # Documents
    doc_summaries = [
        DocumentSummary(
            id=str(doc.id),
            document_type=doc.document_type,
            filename=doc.original_filename,
            status=doc.status,
            uploaded_at=doc.uploaded_at,
        )
        for doc in (app.documents or [])
    ]

    applicant_name = None
    if app.applicant:
        applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}"

    servicer_name = None
    if app.assigned_servicer:
        servicer_name = f"{app.assigned_servicer.first_name} {app.assigned_servicer.last_name}"

    return ApplicationResponse(
        id=str(app.id),
        application_number=app.application_number,
        status=app.status,
        loan_product_id=str(app.loan_product_id),
        loan_product_name=app.loan_product.name if app.loan_product else None,
        loan_product_type=app.loan_product.type if app.loan_product else None,
        applicant_id=str(app.applicant_id),
        applicant_name=applicant_name,
        assigned_servicer_id=str(app.assigned_servicer_id) if app.assigned_servicer_id else None,
        assigned_servicer_name=servicer_name,
        personal_info=app.personal_info or {},
        employment_info=app.employment_info or {},
        financial_info=app.financial_info or {},
        property_info=app.property_info or {},
        declarations=app.declarations or {},
        loan_amount=float(app.loan_amount) if app.loan_amount else None,
        down_payment=float(app.down_payment) if app.down_payment else None,
        dti_ratio=float(app.dti_ratio) if app.dti_ratio else None,
        documents=doc_summaries,
        risk_assessment=risk_summary,
        decision=decision_summary,
        submitted_at=app.submitted_at,
        decided_at=app.decided_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    data: ApplicationCreate,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Create a new mortgage application (draft)."""
    # Verify loan product exists
    loan_result = await session.execute(
        select(LoanProduct).where(
            LoanProduct.id == UUID(data.loan_product_id),
            LoanProduct.is_active == True,  # noqa: E712
        )
    )
    loan = loan_result.scalar_one_or_none()
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan product not found or inactive",
        )

    db_user = await _get_or_create_user(user, session)

    # Calculate loan amount from property info if available
    loan_amount = None
    down_payment_val = None
    if data.property_info:
        purchase_price = data.property_info.purchase_price
        dp = data.property_info.down_payment
        if purchase_price and dp:
            loan_amount = purchase_price - dp
            down_payment_val = dp

    app = Application(
        application_number=_generate_application_number(),
        applicant_id=db_user.id,
        loan_product_id=UUID(data.loan_product_id),
        status="draft",
        personal_info=data.personal_info.model_dump() if data.personal_info else {},
        employment_info=data.employment_info.model_dump() if data.employment_info else {},
        financial_info=data.financial_info.model_dump() if data.financial_info else {},
        property_info=data.property_info.model_dump() if data.property_info else {},
        declarations=data.declarations.model_dump() if data.declarations else {},
        loan_amount=loan_amount,
        down_payment=down_payment_val,
    )
    session.add(app)
    await session.commit()

    # Reload with relationships
    return _build_application_response(
        await _get_application_with_access(app.id, user, session)
    )


@router.get("", response_model=PaginatedApplications)
async def list_applications(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    risk_rating: str | None = Query(None, description="Filter by risk band"),
    assigned_to_me: bool = Query(False, description="Show only my assigned applications"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="asc or desc"),
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedApplications:
    """List applications. Applicants see their own; servicers/admins see all."""
    db_user = await _get_or_create_user(user, session)

    query = select(Application).options(
        selectinload(Application.loan_product),
        selectinload(Application.applicant),
        selectinload(Application.assigned_servicer),
        selectinload(Application.risk_assessments),
    )

    # Role-based filtering
    if user.is_applicant and not user.is_loan_servicer and not user.is_admin:
        query = query.where(Application.applicant_id == db_user.id)
    elif assigned_to_me and user.is_loan_servicer:
        query = query.where(Application.assigned_servicer_id == db_user.id)

    # Status filter
    if status_filter:
        query = query.where(Application.status == status_filter)

    # Risk rating filter (requires join to risk_assessment)
    if risk_rating:
        query = query.join(
            RiskAssessment, RiskAssessment.application_id == Application.id
        ).where(RiskAssessment.risk_band == risk_rating)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_column = getattr(Application, sort_by, Application.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    query = query.offset(offset).limit(limit)

    result = await session.execute(query)
    applications = result.scalars().unique().all()

    items = []
    for app in applications:
        applicant_name = None
        if app.applicant:
            applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}"

        servicer_name = None
        if app.assigned_servicer:
            servicer_name = f"{app.assigned_servicer.first_name} {app.assigned_servicer.last_name}"

        # Get latest risk assessment score
        risk_score = None
        risk_band = None
        if app.risk_assessments:
            latest_ra = sorted(
                app.risk_assessments, key=lambda r: r.created_at, reverse=True
            )[0]
            risk_score = float(latest_ra.overall_score) if latest_ra.overall_score else None
            risk_band = latest_ra.risk_band

        items.append(
            ApplicationListItem(
                id=str(app.id),
                application_number=app.application_number,
                status=app.status,
                applicant_name=applicant_name,
                loan_type=app.loan_product.name if app.loan_product else None,
                loan_amount=float(app.loan_amount) if app.loan_amount else None,
                risk_score=risk_score,
                risk_band=risk_band,
                submitted_at=app.submitted_at,
                created_at=app.created_at,
                assigned_servicer=servicer_name,
            )
        )

    return PaginatedApplications(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Get a specific application with full details."""
    app = await _get_application_with_access(application_id, user, session)
    return _build_application_response(app)


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: UUID,
    data: ApplicationUpdate,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Update a draft application. Only the applicant can update, and only while in draft status."""
    app = await _get_application_with_access(
        application_id, user, session, require_owner=True
    )

    if app.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft applications can be updated",
        )

    # Update loan product if provided
    if data.loan_product_id:
        loan_result = await session.execute(
            select(LoanProduct).where(
                LoanProduct.id == UUID(data.loan_product_id),
                LoanProduct.is_active == True,  # noqa: E712
            )
        )
        loan = loan_result.scalar_one_or_none()
        if loan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan product not found or inactive",
            )
        app.loan_product_id = UUID(data.loan_product_id)

    # Update JSONB fields if provided
    if data.personal_info is not None:
        app.personal_info = data.personal_info.model_dump()
    if data.employment_info is not None:
        app.employment_info = data.employment_info.model_dump()
    if data.financial_info is not None:
        app.financial_info = data.financial_info.model_dump()
    if data.property_info is not None:
        app.property_info = data.property_info.model_dump()
        # Recalculate loan amount
        if data.property_info.purchase_price and data.property_info.down_payment:
            app.loan_amount = data.property_info.purchase_price - data.property_info.down_payment
            app.down_payment = data.property_info.down_payment
    if data.declarations is not None:
        app.declarations = data.declarations.model_dump()

    await session.commit()

    # Reload with relationships
    return _build_application_response(
        await _get_application_with_access(application_id, user, session)
    )


@router.post("/{application_id}/submit", response_model=ApplicationSubmitResponse)
async def submit_application(
    application_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ApplicationSubmitResponse:
    """Submit a draft application for review. Triggers document validation and AI risk assessment."""
    app = await _get_application_with_access(
        application_id, user, session, require_owner=True
    )

    if app.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application cannot be submitted from '{app.status}' status",
        )

    # Validate required fields
    errors = []
    if not app.personal_info or not app.personal_info.get("first_name"):
        errors.append("Personal information is required")
    if not app.employment_info or not app.employment_info.get("employment_status"):
        errors.append("Employment information is required")
    if not app.financial_info:
        errors.append("Financial information is required")
    if not app.property_info or not app.property_info.get("property_type"):
        errors.append("Property information is required")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application is incomplete: {'; '.join(errors)}",
        )

    now = datetime.now(UTC)
    app.status = "submitted"
    app.submitted_at = now

    # Calculate DTI if we have the data
    employment = app.employment_info or {}
    financial = app.financial_info or {}
    annual_income = employment.get("annual_income", 0)
    if annual_income > 0:
        monthly_income = annual_income / 12
        monthly_debts_data = financial.get("monthly_debts", {})
        total_monthly_debts = sum(
            monthly_debts_data.get(k, 0)
            for k in ["car_loan", "student_loans", "credit_cards", "other"]
        )
        app.dti_ratio = (total_monthly_debts / monthly_income) * 100

    await session.commit()

    # Trigger async processing: documents first, then risk assessment
    app_id_str = str(app.id)
    process_application_documents.delay(app_id_str)
    run_risk_assessment.apply_async(
        args=[app_id_str],
        countdown=5,  # Small delay to let document processing start first
    )

    # Notify via WebSocket
    await publish_event(f"application:{app_id_str}", {
        "type": "status_change",
        "data": {"status": "submitted", "application_id": app_id_str},
    })
    await publish_event("servicer:notifications", {
        "type": "new_application",
        "data": {
            "application_id": app_id_str,
            "application_number": app.application_number,
        },
    })

    return ApplicationSubmitResponse(
        id=str(app.id),
        status="submitted",
        submitted_at=now,
        message="Application submitted successfully. Risk assessment has been initiated.",
    )


@router.post("/{application_id}/assign")
@require_role(["loan_servicer", "admin"])
async def assign_application(
    application_id: UUID,
    data: ApplicationAssignRequest,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Assign a servicer to an application."""
    app = await _get_application_with_access(application_id, user, session)

    # Verify servicer exists
    servicer_result = await session.execute(
        select(User).where(User.id == UUID(data.servicer_id))
    )
    servicer = servicer_result.scalar_one_or_none()
    if servicer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicer not found",
        )

    app.assigned_servicer_id = UUID(data.servicer_id)
    await session.commit()

    return {
        "message": "Application assigned successfully",
        "application_id": str(app.id),
        "servicer_id": data.servicer_id,
    }
