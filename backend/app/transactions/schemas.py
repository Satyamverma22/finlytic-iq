# app/transactions/schemas.py

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    id: uuid.UUID
    txn_date: date
    description: str
    amount: Decimal
    txn_type: str
    balance: Decimal | None
    category: str | None
    subcategory: str | None
    classification_method: str | None
    confidence: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class UploadSummary(BaseModel):
    filename: str
    rows_received: int
    rows_stored: int
    duplicates_skipped: int
    rows_failed: int
    errors: list[str] = []

class TransactionListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[TransactionResponse]