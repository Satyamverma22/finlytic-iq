# app/credit/emi_math.py

from decimal import Decimal, ROUND_HALF_UP


def calculate_emi(
    principal: Decimal, annual_interest_rate: Decimal, tenure_months: int
) -> Decimal:
    """
    Standard reducing-balance EMI formula:
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    where r is the MONTHLY interest rate (annual_rate / 12 / 100).
    """
    if principal <= 0:
        raise ValueError("principal must be positive")
    if tenure_months <= 0:
        raise ValueError("tenure_months must be positive")
    if annual_interest_rate < 0:
        raise ValueError("annual_interest_rate cannot be negative")

    if annual_interest_rate == 0:
        # zero-interest edge case: the formula below divides by zero at r=0
        emi = principal / tenure_months
        return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    r = (annual_interest_rate / Decimal("100")) / Decimal("12")
    factor = (1 + r) ** tenure_months
    emi = principal * r * factor / (factor - 1)

    return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_total_repayment(emi: Decimal, tenure_months: int) -> Decimal:
    return (emi * tenure_months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_total_interest(total_repayment: Decimal, principal: Decimal) -> Decimal:
    return (total_repayment - principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)