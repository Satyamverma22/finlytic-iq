# app/financial/aggregation.py

import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.transactions.models import Transaction
from app.financial.loan_models import Loan
from app.financial.expense_classification import classify_expense


async def get_monthly_expense_breakdown(
    db: AsyncSession, user_id, year: int, month: int
) -> dict:
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])

    result = await db.execute(
        select(Transaction.category, Transaction.amount).where(
            Transaction.user_id == user_id,
            Transaction.txn_type == "debit",
            Transaction.txn_date >= start,
            Transaction.txn_date <= end,
        )
    )
    rows = result.all()

    essential = Decimal("0")
    discretionary = Decimal("0")
    uncategorized = Decimal("0")

    for category, amount in rows:
        magnitude = abs(amount)
        bucket = classify_expense(category)
        if bucket == "essential":
            essential += magnitude
        elif bucket == "discretionary":
            discretionary += magnitude
        else:
            uncategorized += magnitude

    return {
        "total_expenses": essential + discretionary + uncategorized,
        "essential_expenses": essential,
        "discretionary_expenses": discretionary,
        "uncategorized_expenses": uncategorized,
        "transaction_count": len(rows),
    }


async def get_monthly_debt_payments(db: AsyncSession, user_id) -> Decimal:
    result = await db.execute(
        select(func.coalesce(func.sum(Loan.emi_amount), 0)).where(
            Loan.user_id == user_id, Loan.is_active == True  # noqa: E712
        )
    )
    return Decimal(result.scalar_one())