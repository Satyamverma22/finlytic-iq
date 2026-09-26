# app/financial/metrics.py

from decimal import Decimal


def calculate_savings_ratio(monthly_income: Decimal, monthly_expenses: Decimal) -> Decimal:
    if monthly_income <= 0:
        raise ValueError("monthly_income must be positive")
    return (monthly_income - monthly_expenses) / monthly_income


def calculate_dti(monthly_debt_payments: Decimal, monthly_income: Decimal) -> Decimal:
    if monthly_income <= 0:
        raise ValueError("monthly_income must be positive")
    return monthly_debt_payments / monthly_income


def calculate_emergency_coverage(
    liquid_savings: Decimal, monthly_essential_expenses: Decimal
) -> Decimal | None:
    """
    Returns months of essential expenses covered by liquid savings.
    None if essential expenses are zero — coverage isn't a meaningful
    number to report in that case, not an error to raise.
    """
    if monthly_essential_expenses <= 0:
        return None
    return liquid_savings / monthly_essential_expenses