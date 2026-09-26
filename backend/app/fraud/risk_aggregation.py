# app/fraud/risk_aggregation.py

from app.fraud.rule_engine import CRITICAL_SIGNALS

RISK_LOW_MAX = 3
RISK_MEDIUM_MAX = 9
# score > RISK_MEDIUM_MAX => High


def aggregate_risk(signals: list[str], score: int) -> str:
    """
    Deterministic mapping from rule-engine output to a risk level.
    Two independent paths to 'High':
      1. Cumulative score crosses the threshold (many moderate signals combined), OR
      2. Any single critical signal is present (one severe red flag alone
         is enough, regardless of what else is or isn't in the message).
    """
    if any(signal in CRITICAL_SIGNALS for signal in signals):
        return "High"

    if score <= RISK_LOW_MAX:
        return "Low"
    if score <= RISK_MEDIUM_MAX:
        return "Medium"
    return "High"