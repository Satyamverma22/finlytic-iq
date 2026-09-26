# app/copilot/safety.py

FORBIDDEN_PHRASES = [
    "you are eligible", "you will be approved", "guaranteed approval",
    "definitely safe", "definitely a scam", "100% eligible",
    "your loan will be approved", "guaranteed to", "you qualify for",
]

SAFE_FALLBACK_REPLY = (
    "I can share what the data shows, but I can't confirm eligibility, "
    "approval, or safety with certainty — please verify through the "
    "official source before acting."
)


def contains_overclaim(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in FORBIDDEN_PHRASES)