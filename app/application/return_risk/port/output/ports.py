"""Outbound ports (driven side) for the return-risk context."""
from __future__ import annotations

from typing import Protocol

from app.domain.return_risk.aggregate.assessment import ReturnRiskAssessment
from app.domain.return_risk.vo.snapshot import ReturnHistory


class ReturnRiskRepositoryPort(Protocol):
    async def save(self, assessment: ReturnRiskAssessment) -> ReturnRiskAssessment: ...
    async def find_by_order_id(self, order_id: str) -> ReturnRiskAssessment | None: ...


class ReturnVelocityCounterPort(Protocol):
    async def incr_and_count(self, customer_id: str, window_seconds: int) -> int: ...


class ReturnDecisionCachePort(Protocol):
    async def get(self, order_id: str) -> ReturnRiskAssessment | None: ...
    async def put(self, assessment: ReturnRiskAssessment, ttl_seconds: int) -> None: ...


class CustomerReturnHistoryPort(Protocol):
    async def fetch(self, customer_id: str) -> ReturnHistory: ...
