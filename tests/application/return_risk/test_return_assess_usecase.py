"""ReturnRiskService tests with in-memory fake ports (no DB/Redis/network)."""
from __future__ import annotations

from decimal import Decimal

import pytest
from app.application.return_risk.dto.commands import AssessReturnRiskCommand
from app.application.return_risk.usecase.assess import ReturnRiskService
from app.domain.return_risk.vo.snapshot import ReturnHistory
from app.domain.return_risk.vo.types import CustomerTier, ReturnDecision, ReturnReason

pytestmark = pytest.mark.asyncio


class FakeVelocity:
    def __init__(self, count: int) -> None:
        self.count = count
        self.calls = 0

    async def incr_and_count(self, customer_id: str, window_seconds: int) -> int:
        self.calls += 1
        return self.count


class FakeHistory:
    def __init__(self, history: ReturnHistory) -> None:
        self.history = history
        self.calls = 0

    async def fetch(self, customer_id: str) -> ReturnHistory:
        self.calls += 1
        return self.history


class InMemoryRepo:
    def __init__(self) -> None:
        self.store: dict = {}

    async def save(self, assessment):
        self.store[assessment.order_id] = assessment
        return assessment

    async def find_by_order_id(self, order_id: str):
        return self.store.get(order_id)


class InMemoryCache:
    def __init__(self) -> None:
        self.store: dict = {}

    async def get(self, order_id: str):
        return self.store.get(order_id)

    async def put(self, assessment, ttl_seconds: int) -> None:
        self.store[assessment.order_id] = assessment


def _command(requested="100", reason=ReturnReason.DEFECTIVE, tier=CustomerTier.STANDARD):
    return AssessReturnRiskCommand(
        order_id="o-1",
        customer_id="c-1",
        order_total=Decimal("100"),
        requested_amount=Decimal(requested),
        currency="USD",
        reason=reason,
        tier=tier,
        days_since_order=1,
    )


def _history(rate=0.0, returns_30d=0):
    return ReturnHistory(20, int(rate * 20), rate, Decimal("0"), "USD", returns_30d, None)


def _service(velocity=0, history=None, repo=None, cache=None):
    return ReturnRiskService(
        repository=repo or InMemoryRepo(),
        cache=cache or InMemoryCache(),
        velocity=FakeVelocity(velocity),
        history=FakeHistory(history if history is not None else _history()),
    )


async def test_low_risk_auto_refunds_and_persists_and_caches():
    repo, cache = InMemoryRepo(), InMemoryCache()
    velocity, history = FakeVelocity(0), FakeHistory(_history())
    svc = ReturnRiskService(repo, cache, velocity, history)

    result = await svc.assess(_command("100"))

    assert result.decision is ReturnDecision.AUTO_REFUND
    assert repo.store["o-1"] is result       # persisted
    assert cache.store["o-1"] is result      # cached
    assert velocity.calls == 1               # velocity incremented
    assert history.calls == 1                # history hop performed


async def test_medium_risk_reviews():
    svc = _service(history=_history(rate=0.6))  # +40 -> MEDIUM
    result = await svc.assess(_command("100"))
    assert result.decision is ReturnDecision.REVIEW


async def test_high_risk_denies_on_blocked():
    svc = _service()
    result = await svc.assess(_command(tier=CustomerTier.BLOCKED))
    assert result.decision is ReturnDecision.DENY
    assert result.score == 100


async def test_failsafe_unknown_history_completes_without_crash():
    svc = _service(history=ReturnHistory.unknown())
    result = await svc.assess(_command("100"))
    # Unknown history = zeros -> no history factors -> low risk auto refund.
    assert result.decision is ReturnDecision.AUTO_REFUND
    assert result.score == 0


async def test_cache_hit_short_circuits_velocity_and_history():
    cache = InMemoryCache()
    velocity = FakeVelocity(0)
    history = FakeHistory(_history())
    svc = ReturnRiskService(InMemoryRepo(), cache, velocity, history)

    first = await svc.assess(_command("100"))
    second = await svc.assess(_command("100"))

    assert second is first
    assert velocity.calls == 1
    assert history.calls == 1
