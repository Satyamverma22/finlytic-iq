# app/core/logging_config.py

import logging
import re


SENSITIVE_PATTERNS = [
    (
        re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE),
        '"password": "***"',
    ),
    (
        re.compile(r'"otp"\s*:\s*"?[^",}]*"?', re.IGNORECASE),
        '"otp": "***"',
    ),
    (
        re.compile(r'"access_token"\s*:\s*"[^"]*"', re.IGNORECASE),
        '"access_token": "***"',
    ),
    (
        re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]+", re.IGNORECASE),
        "Bearer ***",
    ),
    (
        re.compile(r"\b\d{12,19}\b"),
        "[REDACTED-NUMBER]",
    ),
]


def mask_sensitive_data(message: str) -> str:
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)

    return message


class SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Uvicorn access logs use structured arguments that its formatter
        # expects to remain unchanged.
        if record.name == "uvicorn.access":
            return True

        try:
            message = record.getMessage()
        except Exception:
            return True

        masked_message = mask_sensitive_data(message)

        record.msg = masked_message
        record.args = ()

        return True


def configure_logging() -> None:
    filter_ = SensitiveDataFilter()

    for name in (
        "",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "audit",
        "copilot",
        "fraud",
    ):
        logging.getLogger(name).addFilter(filter_)