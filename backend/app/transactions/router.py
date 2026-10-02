# app/transactions/router.py

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.consent.dependencies import require_consent
from app.auth.models import User
from app.core.database import get_db
from app.transactions import service
from app.transactions.models import Transaction
from app.transactions.schemas import TransactionListResponse, UploadSummary
from app.audit.service import record_audit


router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("/upload", response_model=UploadSummary)
async def upload_transactions(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    rows = await service.read_csv_upload(file)

    column_map, column_errors = service.validate_columns(rows)

    if column_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=column_errors[0],
        )

    normalized, row_errors = service.normalize_transactions(
        rows,
        column_map,
    )

    new_transactions, duplicate_count = await service.partition_duplicates(
        db,
        current_user.id,
        normalized,
    )

    rows_stored = await service.store_transactions(
        db,
        current_user.id,
        new_transactions,
        file.filename,
    )

    await record_audit(
        db,
        "transactions.upload",
        user_id=current_user.id,
        details={
            "rows_stored": rows_stored,
            "duplicates_skipped": duplicate_count,
            "rows_failed": len(row_errors),
        },
        request=request,
    )

    return UploadSummary(
        filename=file.filename,
        rows_received=len(rows),
        rows_stored=rows_stored,
        duplicates_skipped=duplicate_count,
        rows_failed=len(row_errors),
        errors=row_errors,
    )


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_consent("financial_analysis")),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(Transaction).where(
        Transaction.user_id == current_user.id
    )

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base_query
        .order_by(
            desc(Transaction.txn_date),
            desc(Transaction.created_at),
        )
        .offset(skip)
        .limit(limit)
    )

    transactions = result.scalars().all()

    return TransactionListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=transactions,
    )