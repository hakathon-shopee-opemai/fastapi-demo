"""AssessOrderRiskService tests with in-memory fake ports (no DB/Redis/network)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.application.risk.dto.commands import AssessOrderRiskCommand
from app.application.risk.usecase.assess import AssessOrderRiskService
from app.domain.risk.vo.snapshot import CustomerHistory, OrderLineSnapshot
from app.domain.risk.vo.types import AccountStatus, CustomerTier, RiskDecision, RiskFactorCode

pytestmark = pytest.mark.asyncio


class FakeVelocity:
    def __init__(self, count: int) -> None:
        self.count = count
        self.calls = 0

    async def incr_and_count(self, customer_id: str, window_seconds: int) -> int:
        self.calls += 1
        return self.count


class FakeHistory:
    def __init__(self, history: CustomerHistory) -> None:
        self.history = history

    async def fetch(self, customer_id: str) -> CustomerHistory:
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


def _command(total="100", qty=1):
    return AssessOrderRiskCommand(
        order_id="o-1",
        customer_id="c-1",
        total=Decimal(total),
        currency="USD",
        shipping_country="VN",
        lines=(OrderLineSnapshot("p-1", qty, Decimal("10")),),
    )


def _history(status=AccountStatus.ACTIVE, tier=CustomerTier.STANDARD, count=5):
    return CustomerHistory(status, tier, count, Decimal("1000"), "USD", None)


def _service(velocity=0, history=None):
    return AssessOrderRiskService(
        repository=InMemoryRepo(),
        cache=InMemoryCache(),
        velocity=FakeVelocity(velocity),
        history=FakeHistory(history or _history()),
    )


async def test_low_risk_approves_and_persists():
    repo = InMemoryRepo()
    svc = AssessOrderRiskService(repo, InMemoryCache(), FakeVelocity(0), FakeHistory(_history()))
    result = await svc.assess(_command("100"))
    assert result.decision is RiskDecision.APPROVE
    assert repo.store["o-1"] is result


async def test_medium_risk_reviews():
    svc = _service(velocity=0, history=_history(count=0))
    result = await svc.assess(_command("6000"))
    assert result.decision is RiskDecision.REVIEW  # 25 + 20 = 45


async def test_blocked_rejects():
    svc = _service(history=_history(status=AccountStatus.BLOCKED))
    result = await svc.assess(_command("100"))
    assert result.decision is RiskDecision.REJECT


async def test_cache_hit_short_circuits_velocity():
    cache = InMemoryCache()
    velocity = FakeVelocity(0)
    svc = AssessOrderRiskService(InMemoryRepo(), cache, velocity, FakeHistory(_history()))
    first = await svc.assess(_command("100"))
    second = await svc.assess(_command("100"))
    assert second is first
    assert velocity.calls == 1  # second call served from cache


async def test_history_unavailable_flagged():
    svc = _service(history=CustomerHistory.unknown())
    result = await svc.assess(_command("100"))
    codes = {f.code for f in result.factors}
    assert RiskFactorCode.HISTORY_UNAVAILABLE in codes
    assert RiskFactorCode.NEW_CUSTOMER in codes
