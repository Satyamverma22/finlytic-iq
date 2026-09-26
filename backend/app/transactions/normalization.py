# app/transactions/normalization.py

import hashlib

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Each canonical field maps to a set of acceptable header variations.
# Matching is case-insensitive and ignores surrounding whitespace/underscores.
COLUMN_ALIASES: dict[str, set[str]] = {
    "date": {"date", "txn date", "transaction date", "value date", "posting date"},
    "description": {"description", "narration", "particulars", "details", "remarks"},
    "amount": {"amount", "txn amount", "transaction amount", "value"},
    "type": {"type", "txn type", "dr/cr", "debit/credit"},
    "balance": {"balance", "closing balance", "running balance", "available balance"},
}

REQUIRED_FIELDS = {"date", "description", "amount"}


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace("_", " ")


def map_columns(headers: list[str]) -> tuple[dict[str, str], list[str]]:
    """
    Returns (column_map, errors).
    column_map: canonical field name -> actual CSV header name, for matched fields only.
    errors: human-readable problems, e.g. missing required fields.
    """
    normalized_to_original = {_normalize_header(h): h for h in headers}

    column_map: dict[str, str] = {}
    for canonical_field, aliases in COLUMN_ALIASES.items():
        for norm_header, original_header in normalized_to_original.items():
            if norm_header in aliases:
                column_map[canonical_field] = original_header
                break

    errors: list[str] = []
    missing_required = REQUIRED_FIELDS - column_map.keys()
    if missing_required:
        errors.append(
            f"Missing required column(s): {', '.join(sorted(missing_required))}. "
            f"Found columns: {', '.join(headers)}."
        )

    return column_map, errors


DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d %b %Y",
    "%d-%b-%Y",
]


def parse_date(value: str) -> date:
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognized date format: '{value}'")


def parse_amount(value: str) -> Decimal:
    cleaned = (
        value.strip()
        .replace(",", "")
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .strip()
    )
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    if negative:
        cleaned = cleaned[1:-1]

    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"unrecognized amount format: '{value}'")

    return -amount if negative else amount


def infer_txn_type(amount: Decimal, raw_type: str | None) -> str:
    if raw_type:
        t = raw_type.strip().lower()
        if t in ("debit", "dr", "d"):
            return "debit"
        if t in ("credit", "cr", "c"):
            return "credit"
    return "debit" if amount < 0 else "credit"


def normalize_amount_sign(amount: Decimal, txn_type: str) -> Decimal:
    magnitude = abs(amount)
    return -magnitude if txn_type == "debit" else magnitude


@dataclass
class NormalizedTransaction:
    txn_date: date
    description: str
    amount: Decimal
    txn_type: str
    balance: Decimal | None


def normalize_rows(
    rows: list[dict], column_map: dict[str, str]
) -> tuple[list[NormalizedTransaction], list[str]]:
    normalized: list[NormalizedTransaction] = []
    errors: list[str] = []

    for i, row in enumerate(rows, start=2):  # row 1 is the header
        try:
            raw_date = row.get(column_map["date"], "")
            raw_description = row.get(column_map["description"], "")
            raw_amount = row.get(column_map["amount"], "")

            if not raw_date.strip() or not raw_description.strip() or not raw_amount.strip():
                raise ValueError("missing a required value (date, description, or amount)")

            txn_date = parse_date(raw_date)
            amount = parse_amount(raw_amount)
            description = raw_description.strip()

            raw_type = row.get(column_map["type"]) if "type" in column_map else None
            txn_type = infer_txn_type(amount, raw_type)
            amount = normalize_amount_sign(amount, txn_type)

            balance = None
            if "balance" in column_map:
                raw_balance = row.get(column_map["balance"], "")
                if raw_balance and raw_balance.strip():
                    balance = parse_amount(raw_balance)

            normalized.append(
                NormalizedTransaction(
                    txn_date=txn_date,
                    description=description,
                    amount=amount,
                    txn_type=txn_type,
                    balance=balance,
                )
            )
        except ValueError as e:
            errors.append(f"Row {i}: {e}")

    return normalized, errors

def compute_dedupe_hash(user_id: str, txn: "NormalizedTransaction") -> str:
    raw = f"{user_id}|{txn.txn_date.isoformat()}|{txn.description.strip().lower()}|{txn.amount}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()