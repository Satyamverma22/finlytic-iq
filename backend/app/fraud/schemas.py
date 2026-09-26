import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FraudInputType = Literal[
    "sms", "email", "whatsapp", "url", "upi_id",
    "investment_offer", "call_transcript", "payment_request",
]


class FraudAnalyseTextRequest(BaseModel):
    input_type: FraudInputType
    text: str = Field(min_length=1, max_length=5000)


class FraudScanResponse(BaseModel):
    id: uuid.UUID
    input_type: str
    risk_level: str
    risk_score: int
    detected_signals: list[str]
    scam_category: str | None
    explanation: str | None
    recommended_action: str | None
    urls_found: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FraudScanListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[FraudScanResponse]