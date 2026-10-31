"""Redis fixed-window velocity counter for return-assessment bursts per customer."""
from __future__ import annotations

from redis.asyncio import Redis


class RedisReturnVelocityCounter:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def _key(customer_id: str) -> str:
        return f"return:velocity:{customer_id}:1h"

    async def incr_and_count(self, customer_id: str, window_seconds: int) -> int:
        key = self._key(customer_id)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            count, _ = await pipe.execute()
        return int(count)
