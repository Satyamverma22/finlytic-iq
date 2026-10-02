# app/core/rate_limit.py

from fastapi import Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.redis_client import redis_client


async def _check(key: str, max_requests: int, window_seconds: int) -> None:
    current = await redis_client.incr(key)

    if current == 1:
        await redis_client.expire(key, window_seconds)
        
    if current > max_requests:
        ttl = await redis_client.ttl(key)
        retry_after = ttl if ttl > 0 else window_seconds
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit_by_ip(action: str, max_requests: int, window_seconds: int):
    async def limiter(request: Request):
        ip = request.client.host if request.client else "unknown"
        await _check(f"ratelimit:{action}:ip:{ip}", max_requests, window_seconds)
    return limiter


def rate_limit_by_user(action: str, max_requests: int, window_seconds: int):
    async def limiter(current_user: User = Depends(get_current_user)):
        await _check(f"ratelimit:{action}:user:{current_user.id}", max_requests, window_seconds)
    return limiter

