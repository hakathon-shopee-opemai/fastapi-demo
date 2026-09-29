"""Unit tests for the idempotent, floored velocity adjust used by the cancellation saga."""
from __future__ import annotations

import pytest

from app.adapter.output.cache.risk.velocity import RedisVelocityCounter, compute_new_count


class FakeRedis:
    """Minimal async fake supporting the subset used by RedisVelocityCounter.adjust."""

    def __init__(self, initial: dict[str, str] | None = None) -> None:
        self.store: dict[str, str] = dict(initial or {})

    async def set(self, name, value, nx=False, ex=None):
        if nx and name in self.store:
            return None
        self.store[name] = str(value)
        return True

    async def get(self, name):
        return self.store.get(name)

    async def expire(self, name, ttl):
        return True


def test_compute_new_count_floors_at_zero():
    assert compute_new_count(0, -1) == 0
    assert compute_new_count(3, -1) == 2
    assert compute_new_count(2, +1) == 3


@pytest.mark.asyncio
async def test_adjust_decrements():
    r = FakeRedis({"risk:velocity:c1:1h": "3"})
    res = await RedisVelocityCounter(r).adjust("c1", -1, "op-1")
    assert (res.previous, res.new, res.applied) == (3, 2, True)
    assert r.store["risk:velocity:c1:1h"] == "2"


@pytest.mark.asyncio
async def test_adjust_floors_at_zero():
    r = FakeRedis({"risk:velocity:c1:1h": "0"})
    res = await RedisVelocityCounter(r).adjust("c1", -1, "op-2")
    assert res.new == 0 and res.applied is True


@pytest.mark.asyncio
async def test_adjust_is_idempotent_by_operation_id():
    r = FakeRedis({"risk:velocity:c1:1h": "5"})
    first = await RedisVelocityCounter(r).adjust("c1", -1, "same-op")
    second = await RedisVelocityCounter(r).adjust("c1", -1, "same-op")
    assert first.applied is True and first.new == 4
    assert second.applied is False and second.new == 4  # unchanged on replay
    assert r.store["risk:velocity:c1:1h"] == "4"


@pytest.mark.asyncio
async def test_adjust_increment_compensation():
    r = FakeRedis({"risk:velocity:c1:1h": "2"})
    res = await RedisVelocityCounter(r).adjust("c1", +1, "comp-1")
    assert (res.previous, res.new, res.applied) == (2, 3, True)
