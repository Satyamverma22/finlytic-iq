# app/financial/service.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.financial.models import FinancialProfile
from app.financial.loan_models import Loan
from app.financial.schemas import FinancialProfileUpsert, LoanCreate


async def get_profile(db: AsyncSession, user_id) -> FinancialProfile | None:
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert_profile(
    db: AsyncSession, user_id, payload: FinancialProfileUpsert
) -> FinancialProfile:
    profile = await get_profile(db, user_id)
    if profile is None:
        profile = FinancialProfile(user_id=user_id)
        db.add(profile)

    profile.monthly_income = payload.monthly_income
    profile.liquid_savings = payload.liquid_savings
    profile.emergency_fund_target_months = payload.emergency_fund_target_months

    await db.commit()
    await db.refresh(profile)
    return profile


async def list_loans(db: AsyncSession, user_id, active_only: bool = True) -> list[Loan]:
    query = select(Loan).where(Loan.user_id == user_id)
    if active_only:
        query = query.where(Loan.is_active == True)  # noqa: E712
    result = await db.execute(query.order_by(Loan.created_at.desc()))
    return list(result.scalars().all())


async def create_loan(db: AsyncSession, user_id, payload: LoanCreate) -> Loan:
    loan = Loan(
        user_id=user_id,
        name=payload.name,
        emi_amount=payload.emi_amount,
        outstanding_amount=payload.outstanding_amount,
    )
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return loan


class LoanNotFoundError(Exception):
    pass


async def deactivate_loan(db: AsyncSession, user_id, loan_id) -> Loan:
    result = await db.execute(
        select(Loan).where(Loan.id == loan_id, Loan.user_id == user_id)
    )
    loan = result.scalar_one_or_none()
    if loan is None:
        raise LoanNotFoundError()

    loan.is_active = False
    await db.commit()
    await db.refresh(loan)
    return loan