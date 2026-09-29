"""Redis-backed fixed-window rate limiter as a FastAPI dependency."""
from __future__ import annotations

import time

from fastapi import Request

from app.common.exception.code import ErrorCode
from app.common.exception.model import AppError
from app.config.redis.client import get_redis
from app.config.security.jwt import decode_token
from app.config.settings.settings import get_settings


def _principal(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            return f"user:{decode_token(auth[7:])['sub']}"
        except AppError:
            pass
    client = request.client
    return f"ip:{client.host if client else 'unknown'}"


async def rate_limit(request: Request) -> None:
    """Enforce a per-principal fixed-window limit; raise 429 when exceeded."""
    settings = get_settings()
    window = settings.rate_limit_window_seconds
    capacity = settings.rate_limit_capacity
    now = int(time.time())
    window_start = now - (now % window)
    key = f"ratelimit:{_principal(request)}:{window_start}"

    redis = get_redis()
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window)
    if count > capacity:
        retry_after = window_start + window - now
        raise AppError(
            ErrorCode.RATE_LIMITED,
            429,
            f"Rate limit exceeded ({capacity} per {window}s)",
            headers={"Retry-After": str(max(retry_after, 1))},
        )
