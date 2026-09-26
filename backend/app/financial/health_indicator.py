# app/financial/health_indicator.py

from dataclasses import dataclass, field
from decimal import Decimal

from app.financial.metrics_service import FinancialMetricsResult

# Thresholds — named constants, not magic numbers scattered through the logic below.
SAVINGS_RATIO_GOOD = Decimal("0.20")
SAVINGS_RATIO_MODERATE = Decimal("0.10")

DTI_HEALTHY = Decimal("0.30")
DTI_MODERATE = Decimal("0.40")
DTI_HIGH = Decimal("0.50")

EMERGENCY_COVERAGE_FULL = Decimal("1.0")     # 100% of target months
EMERGENCY_COVERAGE_PARTIAL = Decimal("0.5")  # 50% of target months

UNCATEGORIZED_WARNING_RATIO = Decimal("0.15")  # 15% of spend unexplained


@dataclass
class HealthIndicatorResult:
    category: str  # "Good" | "Moderate" | "At Risk" | "Poor"
    positive_factors: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    data_limitations: list[str] = field(default_factory=list)


def _score_savings_ratio(ratio: Decimal, positives: list, risks: list, steps: list) -> int:
    if ratio >= SAVINGS_RATIO_GOOD:
        positives.append(f"Savings ratio is {ratio:.1%}, which is a healthy buffer above income.")
        return 2
    if ratio >= SAVINGS_RATIO_MODERATE:
        positives.append(f"Savings ratio is {ratio:.1%}, a reasonable starting point.")
        steps.append("Look for opportunities to increase savings ratio toward 20%.")
        return 1
    if ratio >= 0:
        risks.append(f"Savings ratio is only {ratio:.1%} — little income is left after expenses.")
        steps.append("Review discretionary spending to free up monthly savings.")
        return 0
    risks.append(f"Expenses currently exceed income (savings ratio {ratio:.1%}).")
    steps.append("Monthly expenses exceed income — this needs urgent review.")
    return -2


def _score_dti(dti: Decimal, positives: list, risks: list, steps: list) -> int:
    if dti < DTI_HEALTHY:
        positives.append(f"Debt-to-income ratio is {dti:.1%}, within a generally healthy range.")
        return 2
    if dti < DTI_MODERATE:
        risks.append(f"Debt-to-income ratio is {dti:.1%} — moderate repayment pressure.")
        steps.append("Compare debt-reduction scenarios using the What-If Simulator.")
        return 0
    if dti < DTI_HIGH:
        risks.append(f"Debt-to-income ratio is {dti:.1%} — repayment pressure is elevated.")
        steps.append("Consider prioritizing debt reduction before taking on new EMIs.")
        return -1
    risks.append(f"Debt-to-income ratio is {dti:.1%} — a large share of income goes to debt.")
    steps.append("Debt burden is high; avoid new loans and review existing EMI terms.")
    return -2


def _score_emergency_coverage(
    coverage_months: Decimal | None, target_months: int, positives: list, risks: list,
    steps: list, limitations: list,
) -> int:
    if coverage_months is None:
        limitations.append(
            "Emergency-fund coverage could not be calculated — no essential expenses recorded yet."
        )
        return 0

    ratio_of_target = coverage_months / Decimal(target_months)
    if ratio_of_target >= EMERGENCY_COVERAGE_FULL:
        positives.append(
            f"Liquid savings cover about {coverage_months:.1f} months of essential expenses, "
            f"meeting the {target_months}-month target."
        )
        return 2
    if ratio_of_target >= EMERGENCY_COVERAGE_PARTIAL:
        risks.append(
            f"Liquid savings cover about {coverage_months:.1f} of the targeted "
            f"{target_months} months of essential expenses."
        )
        steps.append("Gradually build emergency savings toward your target coverage.")
        return 0
    risks.append(
        f"Emergency reserve covers only about {coverage_months:.1f} months of essential "
        f"expenses, below the {target_months}-month target."
    )
    steps.append("Emergency fund is low — prioritize building this before other goals.")
    return -1


def build_health_indicator(result: FinancialMetricsResult) -> HealthIndicatorResult:
    positives: list[str] = []
    risks: list[str] = []
    steps: list[str] = []
    limitations: list[str] = []

    score = 0
    score += _score_savings_ratio(result.savings_ratio, positives, risks, steps)
    score += _score_dti(result.dti, positives, risks, steps)
    score += _score_emergency_coverage(
        result.emergency_coverage_months,
        result.emergency_fund_target_months,
        positives, risks, steps, limitations,
    )

    if result.monthly_expenses > 0:
        uncategorized_ratio = result.uncategorized_expenses / result.monthly_expenses
        if uncategorized_ratio >= UNCATEGORIZED_WARNING_RATIO:
            limitations.append(
                f"About {uncategorized_ratio:.0%} of this month's spending is uncategorized, "
                "so this analysis may be incomplete."
            )

    if result.transaction_count == 0:
        limitations.append("No transactions were found for this period.")

    if score >= 3:
        category = "Good"
    elif score >= 0:
        category = "Moderate"
    elif score >= -3:
        category = "At Risk"
    else:
        category = "Poor"

    return HealthIndicatorResult(
        category=category,
        positive_factors=positives,
        risk_factors=risks,
        next_steps=steps,
        data_limitations=limitations,
    )