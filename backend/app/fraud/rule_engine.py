# app/fraud/rule_engine.py

import re

from dataclasses import dataclass


@dataclass
class FraudRule:
    pattern: re.Pattern
    signal: str
    weight: int


def _rule(regex: str, signal: str, weight: int) -> FraudRule:
    return FraudRule(
        pattern=re.compile(regex, re.IGNORECASE),
        signal=signal,
        weight=weight,
    )


# Weights are relative severity, not calibrated probabilities — see
# risk_aggregation.py (Step 3) for how these combine into a risk level.
FRAUD_RULES: list[FraudRule] = [
    # Credential/secret requests
    _rule(
        r"\b(share|send|provide|enter|confirm|tell\s+(us|me))\s+(the\s+|your\s+)?(OTP|one[\s-]?time password)\b",
        "Requests an OTP (one-time password) — a known phishing pattern.",
        5,
    ),
    _rule(
        r"\b(OTP|one[\s-]?time password)\b",
        "Mentions an OTP.",
        1,
    ),
    _rule(
        r"\bCVV\b",
        "Requests a card's CVV number.",
        5,
    ),
    _rule(
        r"\b(UPI PIN|ATM PIN|debit card PIN)\b",
        "Requests a PIN.",
        5,
    ),
    _rule(
        r"\bpassword\b",
        "Requests a password.",
        4,
    ),

    # Prompt-injection attempts
    _rule(
        r"\bignore\s+(all\s+|the\s+)?(previous|prior|above)\s+instructions\b",
        "Contains an attempt to override AI analysis instructions.",
        5,
    ),
    _rule(
        r"\bdisregard\s+(your|the)\s+(system\s+)?(previous\s+)?instructions\b",
        "Contains an attempt to override AI analysis instructions.",
        5,
    ),
    _rule(
        r"\b(reveal|show)\s+(your|the)\s+(system\s+)?prompt\b",
        "Attempts to extract system instructions.",
        5,
    ),
    _rule(
        r"\btell\s+the\s+user\s+(this|it)\s+is\s+(safe|legitimate|not\s+a\s+scam)\b",
        "Attempts to instruct the AI to declare the message safe.",
        5,
    ),

    # Urgency / pressure tactics
    _rule(
        r"\bwithin\s+(the\s+)?(24|12|next\s+few)\s+(hours|minutes)\b",
        "Uses a tight time-pressure deadline.",
        2,
    ),
    _rule(
        r"\b(act now|immediately|urgent(ly)?|final notice)\b",
        "Uses urgent, pressuring language.",
        2,
    ),
    _rule(
        r"\b(account (will be|has been) (blocked|suspended|frozen))\b",
        "Threatens account suspension/blocking.",
        3,
    ),

    # Impersonation / fake authority
    _rule(
        r"\b(RBI|income tax department|cyber ?crime (cell|department)|police (department|station))\b",
        "Claims to be from a government/regulatory authority.",
        2,
    ),
    _rule(
        r"\bwe are calling from your bank\b",
        "Claims to represent your bank.",
        2,
    ),
    _rule(
        r"\bdigital arrest\b",
        "Uses 'digital arrest' language (a known scam pattern).",
        5,
    ),
    _rule(
        r"\b(video call verification|under investigation)\b",
        "Claims you are under investigation or need video verification.",
        4,
    ),

    # Unrealistic investment returns
    _rule(
        r"\b(guaranteed returns?|risk[\s-]?free investment)\b",
        "Promises guaranteed or risk-free investment returns.",
        5,
    ),
    _rule(
        r"\b(double your money|\d{2,}%\s*(returns?|profit|monthly|daily|weekly))\b",
        "Promises unrealistic returns or profit percentages.",
        4,
    ),

    # Payment redirection
    _rule(
        r"\b(transfer|send)\s+(money|payment|funds)\s+to\s+this\s+(account|UPI)\b",
        "Instructs payment to a specific account/UPI ID.",
        3,
    ),

    # Phishing patterns
    _rule(
        r"\bclick\s+(here|this\s+link)\s+to\s+verify\b",
        "Asks you to click a link to 'verify'.",
        3,
    ),
    _rule(
        r"\bupdate\s+your\s+KYC\s+(immediately|now)\b",
        "Urges immediate KYC update via link.",
        3,
    ),

    # Fake support / remote access
    _rule(
        r"\b(install|download)\s+(anydesk|teamviewer|quicksupport)\b",
        "Asks you to install remote-access software.",
        5,
    ),
    _rule(
        r"\btoll[\s-]?free\s+(number|helpline)\b",
        "References a toll-free support number.",
        1,
    ),
]


SUSPICIOUS_URL_PATTERNS = [
    _rule(
        r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        "Contains a raw IP-address URL (not a domain name).",
        4,
    ),
    _rule(
        r"https?://(bit\.ly|tinyurl\.com|t\.co|goo\.gl)/",
        "Contains a shortened URL (destination is hidden).",
        3,
    ),
    _rule(
        r"https?://[a-z0-9-]*(secure|verify|update|confirm)[a-z0-9-]*\.(?!gov\.in|nic\.in)",
        "Contains a URL with security-themed wording on a non-government domain.",
        3,
    ),
]


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s]+", text)


def run_fraud_rules(text: str) -> tuple[list[str], int]:
    """
    Returns (detected_signals, risk_score). Deterministic, no LLM.

    Every signal is a factual observation about the TEXT
    ('contains X pattern'), never a conclusion about whether it IS fraud.
    """
    signals: list[str] = []
    score = 0

    for rule in FRAUD_RULES:
        if rule.pattern.search(text):
            signals.append(rule.signal)
            score += rule.weight

    for rule in SUSPICIOUS_URL_PATTERNS:
        if rule.pattern.search(text):
            signals.append(rule.signal)
            score += rule.weight

    return signals, score


# Signals severe enough that their presence ALONE should floor the risk
# level at High, regardless of total score.
#
# Derived from rule weight, not hand-maintained separately.
CRITICAL_WEIGHT_THRESHOLD = 5

CRITICAL_SIGNALS: set[str] = {
    rule.signal
    for rule in (*FRAUD_RULES, *SUSPICIOUS_URL_PATTERNS)
    if rule.weight >= CRITICAL_WEIGHT_THRESHOLD
}