"""
Loan product routes - browse available mortgage products and check eligibility.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import LoanProduct, get_db

from ..core.security import TokenUser, get_current_user
from ..schemas.loans import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    LoanProductListResponse,
    LoanProductResponse,
)

router = APIRouter()


def _loan_to_response(loan: LoanProduct) -> LoanProductResponse:
    """Convert a LoanProduct model to response schema."""
    return LoanProductResponse(
        id=str(loan.id),
        name=loan.name,
        type=loan.type,
        term_years=loan.term_years,
        rate_type=loan.rate_type,
        min_down_payment_pct=float(loan.min_down_payment_pct),
        min_credit_score=loan.min_credit_score,
        max_dti_ratio=float(loan.max_dti_ratio) if loan.max_dti_ratio else None,
        max_loan_amount=float(loan.max_loan_amount) if loan.max_loan_amount else None,
        description=loan.description,
        eligibility_requirements=loan.eligibility_requirements or [],
        features=loan.features or [],
        is_active=loan.is_active,
    )


@router.get("", response_model=LoanProductListResponse)
async def list_loan_products(
    type: str | None = Query(None, description="Filter by loan type"),
    term: int | None = Query(None, description="Filter by term in years"),
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LoanProductListResponse:
    """List all active loan products with optional filters."""
    query = select(LoanProduct).where(LoanProduct.is_active == True)  # noqa: E712

    if type:
        query = query.where(LoanProduct.type == type)
    if term:
        query = query.where(LoanProduct.term_years == term)

    query = query.order_by(LoanProduct.name)

    # Get total count
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get items
    result = await session.execute(query)
    loans = result.scalars().all()

    return LoanProductListResponse(
        items=[_loan_to_response(loan) for loan in loans],
        total=total,
    )


@router.get("/{loan_id}", response_model=LoanProductResponse)
async def get_loan_product(
    loan_id: UUID,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> LoanProductResponse:
    """Get a specific loan product by ID."""
    result = await session.execute(
        select(LoanProduct).where(LoanProduct.id == loan_id)
    )
    loan = result.scalar_one_or_none()

    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan product not found",
        )

    return _loan_to_response(loan)


@router.post("/{loan_id}/eligibility-check", response_model=EligibilityCheckResponse)
async def check_eligibility(
    loan_id: UUID,
    check: EligibilityCheckRequest,
    user: TokenUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> EligibilityCheckResponse:
    """Quick pre-qualification eligibility check for a loan product."""
    result = await session.execute(
        select(LoanProduct).where(LoanProduct.id == loan_id)
    )
    loan = result.scalar_one_or_none()

    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan product not found",
        )

    warnings: list[str] = []
    suggestions: list[str] = []
    eligible = True

    # Calculate loan amount needed
    loan_amount = check.property_value - check.down_payment_amount
    down_payment_pct = (check.down_payment_amount / check.property_value) * 100

    # Parse credit score range (take the lower bound)
    try:
        credit_score_low = int(check.credit_score_range.split("-")[0])
    except (ValueError, IndexError):
        credit_score_low = 0

    # Calculate DTI ratio
    monthly_income = check.annual_income / 12
    # Estimate monthly mortgage payment (rough: loan_amount * 0.006 for ~7% rate)
    estimated_mortgage_payment = loan_amount * 0.006
    total_monthly_obligations = check.monthly_debts + estimated_mortgage_payment
    dti_ratio = (total_monthly_obligations / monthly_income) * 100 if monthly_income > 0 else 999

    # Check minimum credit score
    if loan.min_credit_score and credit_score_low < loan.min_credit_score:
        eligible = False
        warnings.append(
            f"Credit score ({check.credit_score_range}) is below the minimum "
            f"requirement of {loan.min_credit_score}."
        )
    elif loan.min_credit_score and credit_score_low < loan.min_credit_score + 60:
        warnings.append(
            "Credit score is near the minimum threshold. A higher score may "
            "qualify for better rates."
        )

    # Check down payment
    min_dp = float(loan.min_down_payment_pct)
    if down_payment_pct < min_dp:
        eligible = False
        warnings.append(
            f"Down payment ({down_payment_pct:.1f}%) is below the minimum "
            f"requirement of {min_dp:.1f}%."
        )

    # Check DTI ratio
    if loan.max_dti_ratio and dti_ratio > float(loan.max_dti_ratio):
        eligible = False
        warnings.append(
            f"Estimated debt-to-income ratio ({dti_ratio:.1f}%) exceeds the "
            f"maximum of {float(loan.max_dti_ratio):.1f}%."
        )
    elif loan.max_dti_ratio and dti_ratio > float(loan.max_dti_ratio) - 5:
        warnings.append(
            "Debt-to-income ratio is near the maximum threshold."
        )

    # Check max loan amount
    if loan.max_loan_amount and loan_amount > float(loan.max_loan_amount):
        eligible = False
        warnings.append(
            f"Requested loan amount (${loan_amount:,.0f}) exceeds the maximum "
            f"of ${float(loan.max_loan_amount):,.0f}."
        )

    # Suggestions
    if down_payment_pct < 20:
        suggestions.append(
            "Consider a larger down payment to avoid PMI (Private Mortgage Insurance)."
        )
    if dti_ratio > 36:
        suggestions.append(
            "Reducing monthly debts could improve your debt-to-income ratio "
            "and potentially qualify you for better rates."
        )

    # Estimate rate based on credit score
    estimated_rate = None
    estimated_monthly = None
    if eligible:
        base_rate = 6.5
        if credit_score_low >= 760:
            base_rate = 6.0
        elif credit_score_low >= 720:
            base_rate = 6.25
        elif credit_score_low >= 680:
            base_rate = 6.5
        elif credit_score_low >= 640:
            base_rate = 6.75
        else:
            base_rate = 7.0

        rate_high = base_rate + 0.5
        estimated_rate = f"{base_rate:.1f}% - {rate_high:.1f}%"

        # Monthly payment estimate (P&I only)
        monthly_rate = base_rate / 100 / 12
        n_payments = loan.term_years * 12
        if monthly_rate > 0:
            estimated_monthly = loan_amount * (
                monthly_rate * (1 + monthly_rate) ** n_payments
            ) / ((1 + monthly_rate) ** n_payments - 1)

    return EligibilityCheckResponse(
        eligible=eligible,
        estimated_rate=estimated_rate,
        estimated_monthly_payment=round(estimated_monthly, 2) if estimated_monthly else None,
        max_loan_amount=float(loan.max_loan_amount) if loan.max_loan_amount else None,
        warnings=warnings,
        suggestions=suggestions,
    )
