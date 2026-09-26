# app/transactions/service.py

import csv
import io

from fastapi import UploadFile, HTTPException, status
from app.transactions.normalization import (
    NormalizedTransaction,
    compute_dedupe_hash,
    map_columns,
    normalize_rows,
)
from app.transactions.categorization import categorize_transaction


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.transactions.models import Transaction

ALLOWED_EXTENSION = ".csv"
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


async def read_csv_upload(file: UploadFile) -> list[dict]:
    if not file.filename or not file.filename.lower().endswith(ALLOWED_EXTENSION):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted.",
        )

    raw_bytes = await file.read()

    if len(raw_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if len(raw_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB upload limit.",
        )

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded text.",
        )

    reader = csv.DictReader(io.StringIO(text))
    return list(reader)

def validate_columns(rows: list[dict]) -> tuple[dict[str, str], list[str]]:
    if not rows:
        return {}, ["The CSV has no data rows."]

    headers = list(rows[0].keys())
    return map_columns(headers)

# app/transactions/service.py
# (add this import)
from app.transactions.normalization import normalize_rows, NormalizedTransaction

# (add this function)
def normalize_transactions(
    rows: list[dict], column_map: dict[str, str]
) -> tuple[list[NormalizedTransaction], list[str]]:
    return normalize_rows(rows, column_map)


# (add this function)
async def partition_duplicates(
    db: AsyncSession,
    user_id,
    normalized: list[NormalizedTransaction],
) -> tuple[list[tuple[NormalizedTransaction, str]], int]:
    """
    Returns (new_transactions_with_hash, duplicate_count).
    Catches duplicates both against already-stored transactions (DB)
    and against other rows within this same upload (in-batch).
    """
    hashes = [compute_dedupe_hash(str(user_id), txn) for txn in normalized]

    result = await db.execute(
        select(Transaction.dedupe_hash).where(
            Transaction.user_id == user_id,
            Transaction.dedupe_hash.in_(hashes),
        )
    )
    existing_hashes = {row[0] for row in result.all()}

    new_transactions: list[tuple[NormalizedTransaction, str]] = []
    seen_in_batch: set[str] = set()
    duplicate_count = 0

    for txn, h in zip(normalized, hashes):
        if h in existing_hashes or h in seen_in_batch:
            duplicate_count += 1
            continue
        seen_in_batch.add(h)
        new_transactions.append((txn, h))

    return new_transactions, duplicate_count


# (replace the loop body inside store_transactions)
async def store_transactions(
    db: AsyncSession,
    user_id,
    new_transactions: list[tuple[NormalizedTransaction, str]],
    source_file: str,
) -> int:
    for txn, dedupe_hash in new_transactions:
        category, subcategory, confidence = categorize_transaction(txn.description)
        db.add(
            Transaction(
                user_id=user_id,
                txn_date=txn.txn_date,
                description=txn.description,
                amount=txn.amount,
                txn_type=txn.txn_type,
                balance=txn.balance,
                category=category,
                subcategory=subcategory,
                classification_method="rule" if category else None,
                confidence=confidence,
                dedupe_hash=dedupe_hash,
                source_file=source_file,
            )
        )
    await db.commit()
    return len(new_transactions)