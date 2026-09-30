"""Redis fixed-window velocity counter (real-time in-flight order rate per customer).

Adds an idempotent, floored `adjust()` used by the Order Cancellation Saga to
compensate/reverse a customer's velocity (delta -1 to cancel, +1 to compensate).
"""
from __future__ import annotations

from typing import NamedTuple

from redis.asyncio import Redis


def compute_new_count(current: int, delta: int) -> int:
    """Apply a signed delta to a velocity count, floored at zero (never negative)."""
    return max(0, current + delta)


class AdjustResult(NamedTuple):
    previous: int
    new: int
    applied: bool


class RedisVelocityCounter:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def _key(customer_id: str) -> str:
        return f"risk:velocity:{customer_id}:1h"

    @staticmethod
    def _op_key(operation_id: str) -> str:
        return f"risk:velocity:op:{operation_id}"

    async def incr_and_count(self, customer_id: str, window_seconds: int) -> int:
        key = self._key(customer_id)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            count, _ = await pipe.execute()
        return int(count)

    async def incr_sku_and_count(self, product_id: str, window_seconds: int) -> int:
        """Count how often a SKU was ordered in the window (flash-fraud on hot items)."""
        key = f"risk:velocity:sku:{product_id}:1h"
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            count, _ = await pipe.execute()
        return int(count)

    async def adjust(
        self,
        customer_id: str,
        delta: int,
        operation_id: str,
        window_seconds: int = 3600,
        op_ttl: int = 3600,
    ) -> AdjustResult:
        """Idempotently add `delta` to the velocity count, floored at 0.

        Idempotency: the first call for a given operation_id applies the delta and
        records the op (SET NX EX); any later call with the same operation_id is a
        no-op (applied=False), which makes saga retries and compensations safe.
        """
        key = self._key(customer_id)
        op_key = self._op_key(operation_id)
        acquired = await self._redis.set(op_key, "1", nx=True, ex=op_ttl)
        current = int(await self._redis.get(key) or 0)
        if not acquired:
            return AdjustResult(current, current, False)
        new = compute_new_count(current, delta)
        await self._redis.set(key, new)
        await self._redis.expire(key, window_seconds)
        return AdjustResult(current, new, True)
