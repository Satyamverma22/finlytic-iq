# app/financial/metrics_service.py

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.financial import aggregation, metrics
from app.financial.service import get_profile


class ProfileNotSetError(Exception):
    pass


@dataclass
class FinancialMetricsResult:
    monthly_income: Decimal
    monthly_expenses: Decimal
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    uncategorized_expenses: Decimal
    monthly_surplus: Decimal
    savings_ratio: Decimal
    monthly_debt_payments: Decimal
    dti: Decimal
    liquid_savings: Decimal
    emergency_fund_target_months: int
    emergency_coverage_months: Decimal | None
    transaction_count: int


async def compute_metrics(
    db: AsyncSession, user_id, year: int, month: int
) -> FinancialMetricsResult:
    profile = await get_profile(db, user_id)
    if profile is None:
        raise ProfileNotSetError()

    breakdown = await aggregation.get_monthly_expense_breakdown(db, user_id, year, month)
    debt_payments = await aggregation.get_monthly_debt_payments(db, user_id)

    return FinancialMetricsResult(
        monthly_income=profile.monthly_income,
        monthly_expenses=breakdown["total_expenses"],
        essential_expenses=breakdown["essential_expenses"],
        discretionary_expenses=breakdown["discretionary_expenses"],
        uncategorized_expenses=breakdown["uncategorized_expenses"],
        monthly_surplus=profile.monthly_income - breakdown["total_expenses"],
        savings_ratio=metrics.calculate_savings_ratio(profile.monthly_income, breakdown["total_expenses"]),
        monthly_debt_payments=debt_payments,
        dti=metrics.calculate_dti(debt_payments, profile.monthly_income),
        liquid_savings=profile.liquid_savings,
        emergency_fund_target_months=profile.emergency_fund_target_months,
        emergency_coverage_months=metrics.calculate_emergency_coverage(
            profile.liquid_savings, breakdown["essential_expenses"]
        ),
        transaction_count=breakdown["transaction_count"],
    )