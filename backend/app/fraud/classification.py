# app/fraud/classification.py

import json
import re

from app.ai.llm_service import LLMProvider

SCAM_CATEGORIES = {
    "Phishing",
    "Investment Scam",
    "UPI Scam",
    "Impersonation",
    "Fake Customer Support",
    "Digital Arrest",
    "Payment Fraud",
    "Account Takeover Attempt",
    "Unclear",
}

FRAUD_SYSTEM_PROMPT = """You are a fraud-awareness assistant for the Financial \
Compass platform. You are given signals that a DETERMINISTIC rule engine has \
ALREADY detected in a message, plus a RISK LEVEL that has ALREADY been decided.

STRICT RULES:
- You do NOT decide the risk level. It is given to you as a fact. Never \
contradict, soften, or re-derive it.
- You do NOT introduce new red flags beyond the DETECTED SIGNALS list given. \
If you notice something else in the excerpt, ignore it — only the given signals \
count as evidence.
- NEVER state or imply the message definitely IS a scam, or definitely IS safe. \
Use hedged language: "shows signs consistent with...", "resembles a pattern \
commonly seen in...", "these signals are commonly associated with...".
- Choose exactly one scam_category from this fixed list: Phishing, Investment \
Scam, UPI Scam, Impersonation, Fake Customer Support, Digital Arrest, Payment \
Fraud, Account Takeover Attempt, Unclear. Use "Unclear" if the signals don't \
clearly point to one specific category.
- recommended_action must be concrete, practical safety steps (e.g., do not \
share OTP/PIN, do not click the link, verify via the official app/number, do \
not install remote-access software) — grounded in which signals were detected.
- Respond with ONLY valid JSON, no markdown code fences, no extra text, in \
exactly this shape:
{"scam_category": "...", "explanation": "...", "recommended_action": "..."}
"""


def _parse_llm_response(raw: str) -> dict:
    # strip markdown code fences if the model added them despite instructions
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


async def classify_fraud(
    llm: LLMProvider,
    text_excerpt: str,
    signals: list[str],
    risk_level: str,
    urls: list[str],
) -> tuple[str, str, str]:
    """
    Returns (scam_category, explanation, recommended_action).
    Falls back to safe, generic values if the LLM call or JSON parsing
    fails — the risk_level and detected_signals (already computed,
    deterministic) remain valid and usable regardless.
    """
    signals_text = "\n".join(f"- {s}" for s in signals) or "(no rule-based signals detected)"
    urls_text = "\n".join(urls) or "(none found)"

    user_prompt = f"""DETECTED SIGNALS (already found by the rule engine — treat as fact):
{signals_text}

RISK LEVEL (already determined — do not contradict): {risk_level}

URLS FOUND IN MESSAGE:
{urls_text}

MESSAGE EXCERPT (for tone/context only — do not extract new signals from this):
{text_excerpt[:500]}

Respond with the JSON object described in your instructions."""

    try:
        raw_response = await llm.generate(FRAUD_SYSTEM_PROMPT, user_prompt)
        parsed = _parse_llm_response(raw_response)

        category = parsed.get("scam_category", "Unclear")
        if category not in SCAM_CATEGORIES:
            category = "Unclear"

        explanation = parsed.get("explanation") or "No explanation was generated."
        action = parsed.get("recommended_action") or (
            "Do not share OTPs, PINs, or passwords. Do not click unfamiliar links "
            "or install unknown apps. Verify through the institution's official "
            "channel before taking any action."
        )
        return category, explanation, action

    except Exception:
        # LLM/network/parsing failure — the deterministic risk_level and
        # signals are still valid and already computed; this scan should
        # NEVER be blocked or lost just because the narrative layer failed.
        return (
            "Unclear",
            "An automated explanation could not be generated for this message. "
            "Review the detected signals above directly.",
            "Do not share OTPs, PINs, or passwords. Do not click unfamiliar links "
            "or install unknown apps. Verify through the institution's official "
            "channel before taking any action.",
        )