# app/schemes/router.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.consent.dependencies import require_consent
from app.auth.models import User
from app.core.database import get_db
from app.core.rate_limit import rate_limit_by_user
from app.schemes.match_service import match_schemes
from app.schemes.models import Scheme
from app.schemes.schemas import (
    SchemeMatchRequest,
    SchemeMatchResponse,
    SchemeListResponse,
    SchemeSummary,
)


router = APIRouter(prefix="/api/schemes", tags=["schemes"])


@router.post("/match", response_model=SchemeMatchResponse)
async def match(
    payload: SchemeMatchRequest,
    current_user: User = Depends(
        require_consent("personalised_recommendations")
    ),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_by_user("scheme_match", 20, 60)),
):
    results = await match_schemes(db, payload)

    return SchemeMatchResponse(
        query_used=payload.query
        or "government schemes and benefits I may be eligible for",
        candidate_count=len(results),
        results=results,
    )


@router.get("", response_model=SchemeListResponse)
async def list_schemes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count()).select_from(Scheme)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Scheme)
        .order_by(desc(Scheme.created_at))
        .offset(skip)
        .limit(limit)
    )
    schemes = result.scalars().all()

    return SchemeListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[SchemeSummary.model_validate(s) for s in schemes],
    )