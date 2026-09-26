# app/schemes/models.py

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import String, Text, Date, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Scheme(Base):
    __tablename__ = "schemes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    scheme_name: Mapped[str] = mapped_column(String(500), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)  # "national" | "state"

    # structured filtering fields — used for metadata filtering (Phase 6 Step 6),
    # BEFORE vector search ever runs
    states: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    target_groups: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    occupations: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    education_levels: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    business_types: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    min_income: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_income: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    # descriptive fields — used for RAG chunking/embedding (Phase 6 Step 5)
    # and shown directly in cited responses (Phase 6 Step 8)
    benefits: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility_conditions: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    required_documents: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    application_process: Mapped[str | None] = mapped_column(Text, nullable=True)

    # source/provenance — required on every scheme record per the spec's
    # "never claim definite eligibility, always show official source" rule
    official_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    department: Mapped[str] = mapped_column(String(500), nullable=False)
    source_document: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_verified_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )