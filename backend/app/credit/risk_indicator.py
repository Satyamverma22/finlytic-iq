# app/credit/risk_indicator.py

from decimal import Decimal

from app.financial.health_indicator import DTI_HEALTHY, DTI_MODERATE, DTI_HIGH


def build_scenario_risk(
    resulting_dti: Decimal, remaining_cash_flow: Decimal
) -> tuple[str, list[str]]:
    """
    Returns (risk_category, risk_factors).
    Deliberately reuses the exact DTI thresholds from health_indicator.py
    rather than redefining similar-but-different numbers here.
    """
    factors: list[str] = []

    if remaining_cash_flow < 0:
        factors.append(
            f"This scenario would leave a monthly shortfall of "
            f"₹{abs(remaining_cash_flow):,.2f} after expenses and this EMI."
        )
        return "High Risk", factors

    if resulting_dti < DTI_HEALTHY:
        factors.append(f"Resulting debt-to-income ratio would be {resulting_dti:.1%}, a healthy level.")
        category = "Comfortable"
    elif resulting_dti < DTI_MODERATE:
        factors.append(f"Resulting debt-to-income ratio would be {resulting_dti:.1%}, moderate repayment pressure.")
        category = "Manageable"
    elif resulting_dti < DTI_HIGH:
        factors.append(f"Resulting debt-to-income ratio would be {resulting_dti:.1%}, elevated repayment pressure.")
        category = "Elevated Risk"
    else:
        factors.append(f"Resulting debt-to-income ratio would be {resulting_dti:.1%}, a high debt burden.")
        category = "High Risk"

    if remaining_cash_flow < Decimal("5000"):
        factors.append(
            f"Only about ₹{remaining_cash_flow:,.2f} would remain monthly after expenses and this EMI "
            "— little room for unexpected costs."
        )

    return category, factors