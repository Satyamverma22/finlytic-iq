# app/fraud/router.py

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from app.fraud import service
from app.fraud.models import FraudScan
from app.fraud.rule_engine import extract_urls
from app.fraud.schemas import FraudAnalyseTextRequest, FraudScanResponse, FraudScanListResponse

router = APIRouter(prefix="/api/fraud", tags=["fraud"])


def _to_response(scan: FraudScan) -> FraudScanResponse:
    return FraudScanResponse(
        id=scan.id,
        input_type=scan.input_type,
        risk_level=scan.risk_level,
        risk_score=scan.risk_score,
        detected_signals=scan.detected_signals,
        scam_category=scan.scam_category,
        explanation=scan.explanation,
        recommended_action=scan.recommended_action,
        urls_found=extract_urls(scan.raw_input_text),
        created_at=scan.created_at,
    )


@router.post("/analyse-text", response_model=FraudScanResponse, status_code=status.HTTP_201_CREATED)
async def analyse_text(
    payload: FraudAnalyseTextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scan = await service.analyse_text(db, current_user.id, payload)
    return _to_response(scan)



@router.get("/scans", response_model=FraudScanListResponse)
async def list_scans(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(FraudScan).where(FraudScan.user_id == current_user.id)

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(desc(FraudScan.created_at)).offset(skip).limit(limit)
    )
    scans = result.scalars().all()

    return FraudScanListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[_to_response(s) for s in scans],
    )