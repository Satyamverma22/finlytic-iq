# app/schemes/schemas.py

from pydantic import ConfigDict
from decimal import Decimal

from pydantic import BaseModel
import uuid
from datetime import date, datetime

class SchemeSearchProfile(BaseModel):
    """
    Voluntary profile attributes the user provides for scheme matching.
    Every field is optional — an unprovided field means 'unknown', and
    metadata filtering treats unknown as 'don't filter on this dimension',
    never as 'exclude'. This matches the spec's own rule: absence of
    information is a limitation to disclose, not a reason to reject.
    """
    state: str | None = None
    occupation: str | None = None
    education_level: str | None = None
    business_type: str | None = None
    monthly_income: Decimal | None = None
    target_groups: list[str] | None = None



class SchemeMatchRequest(SchemeSearchProfile):
    query: str | None = None


class SchemeMatchResult(BaseModel):
    scheme_id: uuid.UUID
    scheme_name: str
    category: str
    matched: list[str]
    needs_verification: list[str]
    explanation: str
    benefits: str
    required_documents: list[str] | None
    official_url: str
    department: str
    last_verified_date: date


class SchemeMatchResponse(BaseModel):
    query_used: str
    candidate_count: int
    results: list[SchemeMatchResult]


class SchemeSummary(BaseModel):
    id: uuid.UUID
    scheme_name: str
    scope: str
    department: str
    official_url: str
    last_verified_date: date

    model_config = ConfigDict(from_attributes=True)


class SchemeListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[SchemeSummary]