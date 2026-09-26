# app/transactions/models.py

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import String, Date, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    txn_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "debit" | "credit"
    balance: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classification_method: Mapped[str | None] = mapped_column(String(20), nullable=True)  # rule|ml|llm|manual
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)

    # a hash of (user_id, date, description, amount) — used for duplicate detection
    dedupe_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
        Index("ix_transactions_user_dedupe", "user_id", "dedupe_hash", unique=True),
    )