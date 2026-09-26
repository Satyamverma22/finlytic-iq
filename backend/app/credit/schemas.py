# app/credit/schemas.py

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ScenarioCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    proposed_amount: Decimal = Field(gt=0)
    annual_interest_rate: Decimal = Field(ge=0, le=100)
    tenure_months: int = Field(gt=0, le=480)  # 40 years, a generous upper bound


class ScenarioResponse(BaseModel):
    id: uuid.UUID
    label: str
    proposed_amount: Decimal
    annual_interest_rate: Decimal
    tenure_months: int

    snapshot_monthly_income: Decimal
    snapshot_existing_emi: Decimal
    snapshot_monthly_expenses: Decimal

    estimated_emi: Decimal
    total_repayment: Decimal
    total_interest: Decimal
    resulting_dti: Decimal
    remaining_cash_flow: Decimal

    risk_category: str
    risk_factors: list[str]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScenarioListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[ScenarioResponse]


class ScenarioCompareRequest(BaseModel):
    scenario_ids: list[uuid.UUID] = Field(min_length=2, max_length=5)


class ComparisonRow(BaseModel):
    metric: str
    values: list[str]  # one formatted value per scenario, same order as `scenarios`


class ScenarioCompareResponse(BaseModel):
    scenarios: list[ScenarioResponse]
    comparison: list[ComparisonRow]