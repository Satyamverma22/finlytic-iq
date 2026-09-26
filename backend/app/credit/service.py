# app/credit/service.py

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.credit.emi_math import (
    calculate_emi,
    calculate_total_repayment,
    calculate_total_interest,
)
from app.credit.models import CreditScenario
from app.credit.schemas import ScenarioCreate
from app.credit.risk_indicator import build_scenario_risk
from app.financial.metrics import calculate_dti
from app.financial.service import get_profile
from app.financial.aggregation import (
    get_monthly_debt_payments,
    get_monthly_expense_breakdown,
)


class ProfileNotSetError(Exception):
    pass


async def build_and_save_scenario(
    db: AsyncSession, user_id, payload: ScenarioCreate, year: int, month: int
) -> tuple[CreditScenario, str, list[str]]:
    profile = await get_profile(db, user_id)
    if profile is None:
        raise ProfileNotSetError()

    existing_emi = await get_monthly_debt_payments(db, user_id)
    breakdown = await get_monthly_expense_breakdown(db, user_id, year, month)

    emi = calculate_emi(
        payload.proposed_amount,
        payload.annual_interest_rate,
        payload.tenure_months,
    )
    total_repayment = calculate_total_repayment(
        emi, payload.tenure_months
    )
    total_interest = calculate_total_interest(
        total_repayment, payload.proposed_amount
    )

    total_emi_after = existing_emi + emi
    resulting_dti = calculate_dti(
        total_emi_after, profile.monthly_income
    )

    remaining_cash_flow = (
        profile.monthly_income
        - breakdown["total_expenses"]
        - emi
    )

    scenario = CreditScenario(
        user_id=user_id,
        label=payload.label,
        proposed_amount=payload.proposed_amount,
        annual_interest_rate=payload.annual_interest_rate,
        tenure_months=payload.tenure_months,
        snapshot_monthly_income=profile.monthly_income,
        snapshot_existing_emi=existing_emi,
        snapshot_monthly_expenses=breakdown["total_expenses"],
        estimated_emi=emi,
        total_repayment=total_repayment,
        total_interest=total_interest,
        resulting_dti=resulting_dti,
        remaining_cash_flow=remaining_cash_flow,
    )

    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)

    risk_category, risk_factors = build_scenario_risk(
        resulting_dti, remaining_cash_flow
    )

    return scenario, risk_category, risk_factors



class ScenarioNotFoundError(Exception):
    def __init__(self, missing_ids: list):
        self.missing_ids = missing_ids
        super().__init__(f"Scenarios not found or not owned by user: {missing_ids}")


async def get_scenarios_for_comparison(
    db: AsyncSession, user_id, scenario_ids: list
) -> list[CreditScenario]:
    result = await db.execute(
        select(CreditScenario).where(
            CreditScenario.id.in_(scenario_ids),
            CreditScenario.user_id == user_id,
        )
    )
    found = {s.id: s for s in result.scalars().all()}

    missing = [str(sid) for sid in scenario_ids if sid not in found]
    if missing:
        raise ScenarioNotFoundError(missing)

    # preserve the order the caller requested, not DB/insertion order
    return [found[sid] for sid in scenario_ids]