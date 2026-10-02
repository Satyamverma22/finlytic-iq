# app/credit/router.py

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.consent.dependencies import require_consent
from app.auth.models import User
from app.core.database import get_db
from app.credit import service
from app.credit.models import CreditScenario
from app.credit.risk_indicator import build_scenario_risk
from app.credit.schemas import (
    ScenarioCreate,
    ScenarioResponse,
    ScenarioCompareRequest,
    ScenarioCompareResponse,
    ComparisonRow,
    ScenarioListResponse,
)

router = APIRouter(prefix="/api/credit-scenarios", tags=["credit"])


@router.post(
    "",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    payload: ScenarioCreate,
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    try:
        scenario, risk_category, risk_factors = await service.build_and_save_scenario(
            db, current_user.id, payload, today.year, today.month
        )
    except service.ProfileNotSetError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set up your financial profile before running a credit scenario.",
        )

    return ScenarioResponse(
        id=scenario.id,
        label=scenario.label,
        proposed_amount=scenario.proposed_amount,
        annual_interest_rate=scenario.annual_interest_rate,
        tenure_months=scenario.tenure_months,
        snapshot_monthly_income=scenario.snapshot_monthly_income,
        snapshot_existing_emi=scenario.snapshot_existing_emi,
        snapshot_monthly_expenses=scenario.snapshot_monthly_expenses,
        estimated_emi=scenario.estimated_emi,
        total_repayment=scenario.total_repayment,
        total_interest=scenario.total_interest,
        resulting_dti=scenario.resulting_dti,
        remaining_cash_flow=scenario.remaining_cash_flow,
        risk_category=risk_category,
        risk_factors=risk_factors,
        created_at=scenario.created_at,
    )


@router.get("", response_model=ScenarioListResponse)
async def list_scenarios(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(CreditScenario).where(
        CreditScenario.user_id == current_user.id
    )

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base_query
        .order_by(desc(CreditScenario.created_at))
        .offset(skip)
        .limit(limit)
    )
    scenarios = result.scalars().all()

    items = []
    for scenario in scenarios:
        risk_category, risk_factors = build_scenario_risk(
            scenario.resulting_dti,
            scenario.remaining_cash_flow,
        )

        items.append(
            ScenarioResponse(
                id=scenario.id,
                label=scenario.label,
                proposed_amount=scenario.proposed_amount,
                annual_interest_rate=scenario.annual_interest_rate,
                tenure_months=scenario.tenure_months,
                snapshot_monthly_income=scenario.snapshot_monthly_income,
                snapshot_existing_emi=scenario.snapshot_existing_emi,
                snapshot_monthly_expenses=scenario.snapshot_monthly_expenses,
                estimated_emi=scenario.estimated_emi,
                total_repayment=scenario.total_repayment,
                total_interest=scenario.total_interest,
                resulting_dti=scenario.resulting_dti,
                remaining_cash_flow=scenario.remaining_cash_flow,
                risk_category=risk_category,
                risk_factors=risk_factors,
                created_at=scenario.created_at,
            )
        )

    return ScenarioListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )


@router.post("/compare", response_model=ScenarioCompareResponse)
async def compare_scenarios(
    payload: ScenarioCompareRequest,
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    try:
        scenarios = await service.get_scenarios_for_comparison(
            db,
            current_user.id,
            payload.scenario_ids,
        )
    except service.ScenarioNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario(s) not found: {', '.join(e.missing_ids)}",
        )

    scenario_responses = []

    for scenario in scenarios:
        risk_category, risk_factors = build_scenario_risk(
            scenario.resulting_dti,
            scenario.remaining_cash_flow,
        )

        scenario_responses.append(
            ScenarioResponse(
                id=scenario.id,
                label=scenario.label,
                proposed_amount=scenario.proposed_amount,
                annual_interest_rate=scenario.annual_interest_rate,
                tenure_months=scenario.tenure_months,
                snapshot_monthly_income=scenario.snapshot_monthly_income,
                snapshot_existing_emi=scenario.snapshot_existing_emi,
                snapshot_monthly_expenses=scenario.snapshot_monthly_expenses,
                estimated_emi=scenario.estimated_emi,
                total_repayment=scenario.total_repayment,
                total_interest=scenario.total_interest,
                resulting_dti=scenario.resulting_dti,
                remaining_cash_flow=scenario.remaining_cash_flow,
                risk_category=risk_category,
                risk_factors=risk_factors,
                created_at=scenario.created_at,
            )
        )

    comparison = [
        ComparisonRow(
            metric="Estimated EMI",
            values=[f"₹{s.estimated_emi:,.2f}" for s in scenarios],
        ),
        ComparisonRow(
            metric="Total Interest",
            values=[f"₹{s.total_interest:,.2f}" for s in scenarios],
        ),
        ComparisonRow(
            metric="Resulting DTI",
            values=[f"{s.resulting_dti:.1%}" for s in scenarios],
        ),
        ComparisonRow(
            metric="Remaining Monthly Cash Flow",
            values=[f"₹{s.remaining_cash_flow:,.2f}" for s in scenarios],
        ),
        ComparisonRow(
            metric="Risk Category",
            values=[r.risk_category for r in scenario_responses],
        ),
    ]

    return ScenarioCompareResponse(
        scenarios=scenario_responses,
        comparison=comparison,
    )