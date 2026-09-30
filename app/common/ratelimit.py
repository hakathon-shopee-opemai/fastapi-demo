"""Redis-backed fixed-window rate limiters: a FastAPI dependency and a per-operation decorator."""
from __future__ import annotations

import functools
import time
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from fastapi import Request

from app.common.exception.code import ErrorCode
from app.common.exception.model import AppError
from app.config.redis.client import get_redis
from app.config.security.jwt import decode_token
from app.config.settings.settings import get_settings

P = ParamSpec("P")
T = TypeVar("T")


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


def rate_limited(
    key: str, permits: int, window_seconds: int = 60
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Per-operation fixed-window limit (shared across callers) for one business operation."""

    def decorate(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            now = int(time.time())
            window_start = now - (now % window_seconds)
            bucket = f"ratelimit:op:{key}:{window_start}"
            redis = get_redis()
            count = await redis.incr(bucket)
            if count == 1:
                await redis.expire(bucket, window_seconds)
            if count > permits:
                raise AppError(
                    ErrorCode.RATE_LIMITED,
                    429,
                    f"Too many {key} calls ({permits} per {window_seconds}s)",
                    headers={"Retry-After": str(max(window_start + window_seconds - now, 1))},
                )
            return await fn(*args, **kwargs)

        return wrapper

    return decorate
