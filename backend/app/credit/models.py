# app/credit/models.py

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CreditScenario(Base):
    __tablename__ = "credit_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False)

    # inputs — the proposed new loan being simulated
    proposed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    annual_interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)

    # snapshot of the user's situation AT THE TIME this scenario was run
    snapshot_monthly_income: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    snapshot_existing_emi: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    snapshot_monthly_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # computed outputs
    estimated_emi: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_repayment: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_interest: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    resulting_dti: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    remaining_cash_flow: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )