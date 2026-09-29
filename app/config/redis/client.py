"""Async Redis client management (no connection at import time)."""
from __future__ import annotations

from redis.asyncio import Redis, from_url

_redis: Redis | None = None


def init_redis(redis_url: str) -> None:
    global _redis
    _redis = from_url(redis_url, encoding="utf-8", decode_responses=True)


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
    _redis = None


def get_redis() -> Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized; call init_redis() first.")
    return _redis


async def check_redis() -> bool:
    if _redis is None:
        return False
    try:
        return bool(await _redis.ping())
    except Exception:  # noqa: BLE001 - health check must never raise
        return False
