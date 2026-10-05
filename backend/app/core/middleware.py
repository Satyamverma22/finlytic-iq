# app/core/middleware.py

import logging
import time
import uuid

from fastapi import Request

from app.auth.security import decode_access_token

logger = logging.getLogger("uvicorn.error")


async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.monotonic()

    user_hint = "anonymous"
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        payload = decode_access_token(auth_header[7:])
        if payload and "sub" in payload:
            user_hint = payload["sub"][:8]  # truncated, not the full user id

    response = await call_next(request)
    latency_ms = round((time.monotonic() - start) * 1000, 1)

    logger.info(
        "request_id=%s method=%s path=%s status=%s latency_ms=%s user=%s",
        request_id, request.method, request.url.path, response.status_code, latency_ms, user_hint,
    )
    response.headers["X-Request-ID"] = request_id
    return response