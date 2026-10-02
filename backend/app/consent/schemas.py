# app/consent/schemas.py

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ConsentPurpose = Literal[
    "financial_analysis",
    "fraud_analysis",
    "personalised_recommendations",
    "anonymous_analytics",
]


class ConsentGrantRequest(BaseModel):
    purpose: ConsentPurpose
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class ConsentResponse(BaseModel):
    id: uuid.UUID
    purpose: str
    data_type: str
    recipient: str
    granted_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    status: str  # active | expired | revoked