# app/financial/router.py

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.consent.dependencies import require_consent
from app.auth.models import User
from app.core.database import get_db
from app.financial import service
from app.financial import metrics_service
from app.financial.health_indicator import build_health_indicator
from app.financial.schemas import (
    FinancialProfileUpsert,
    FinancialProfileResponse,
    LoanCreate,
    LoanResponse,
    FinancialHealthResponse,
)

router = APIRouter(prefix="/api/financial", tags=["financial"])


@router.put("/profile", response_model=FinancialProfileResponse)
async def upsert_profile(
    payload: FinancialProfileUpsert,
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    return await service.upsert_profile(db, current_user.id, payload)


@router.get("/profile", response_model=FinancialProfileResponse)
async def get_profile(
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    profile = await service.get_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No financial profile set up yet.",
        )
    return profile


@router.post(
    "/loans",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_loan(
    payload: LoanCreate,
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_loan(db, current_user.id, payload)


@router.get("/loans", response_model=list[LoanResponse])
async def list_loans(
    active_only: bool = True,
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_loans(db, current_user.id, active_only)


@router.patch("/loans/{loan_id}/deactivate", response_model=LoanResponse)
async def deactivate_loan(
    loan_id: uuid.UUID,
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.deactivate_loan(db, current_user.id, loan_id)
    except service.LoanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found.",
        )


@router.get("/health", response_model=FinancialHealthResponse)
async def get_financial_health(
    year: int | None = None,
    month: int | None = None,
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month

    try:
        result = await metrics_service.compute_metrics(
            db,
            current_user.id,
            year,
            month,
        )
    except metrics_service.ProfileNotSetError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set up your financial profile (income, savings) before requesting a health report.",
        )

    indicator = build_health_indicator(result)

    return FinancialHealthResponse(
        period_year=year,
        period_month=month,
        monthly_income=result.monthly_income,
        monthly_expenses=result.monthly_expenses,
        essential_expenses=result.essential_expenses,
        discretionary_expenses=result.discretionary_expenses,
        uncategorized_expenses=result.uncategorized_expenses,
        monthly_surplus=result.monthly_surplus,
        savings_ratio=result.savings_ratio,
        monthly_debt_payments=result.monthly_debt_payments,
        dti=result.dti,
        liquid_savings=result.liquid_savings,
        emergency_fund_target_months=result.emergency_fund_target_months,
        emergency_coverage_months=result.emergency_coverage_months,
        category=indicator.category,
        positive_factors=indicator.positive_factors,
        risk_factors=indicator.risk_factors,
        next_steps=indicator.next_steps,
        data_limitations=indicator.data_limitations,
    )