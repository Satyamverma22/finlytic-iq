# app/fraud/models.py

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FraudScan(Base):
    __tablename__ = "fraud_scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    input_type: Mapped[str] = mapped_column(String(30), nullable=False)  # sms|email|whatsapp|url|upi_id|investment_offer|call_transcript|payment_request
    raw_input_text: Mapped[str] = mapped_column(Text, nullable=False)

    # deterministic outputs (Steps 2-3) — always present, computed before any LLM call
    detected_signals: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)  # Low|Medium|High

    # LLM-generated outputs (Step 4) — grounded in detected_signals, never independent of them
    scam_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )