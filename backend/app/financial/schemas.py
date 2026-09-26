# app/financial/schemas.py

import uuid
from datetime import datetime
from decimal import Decimal


from pydantic import BaseModel, ConfigDict, Field


class FinancialProfileUpsert(BaseModel):
    monthly_income: Decimal = Field(gt=0)
    liquid_savings: Decimal = Field(ge=0, default=Decimal("0"))
    emergency_fund_target_months: int = Field(ge=1, le=24, default=3)


class FinancialProfileResponse(BaseModel):
    id: uuid.UUID
    monthly_income: Decimal
    liquid_savings: Decimal
    emergency_fund_target_months: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    emi_amount: Decimal = Field(gt=0)
    outstanding_amount: Decimal | None = Field(default=None, ge=0)


class LoanResponse(BaseModel):
    id: uuid.UUID
    name: str
    emi_amount: Decimal
    outstanding_amount: Decimal | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)




class FinancialHealthResponse(BaseModel):
    period_year: int
    period_month: int

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

    category: str
    positive_factors: list[str]
    risk_factors: list[str]
    next_steps: list[str]
    data_limitations: list[str]