"""Outbound ports (driven side) for the risk context."""
from __future__ import annotations

from typing import Protocol

from app.domain.risk.aggregate.assessment import RiskAssessment
from app.domain.risk.vo.snapshot import CustomerHistory


class RiskAssessmentRepositoryPort(Protocol):
    async def save(self, assessment: RiskAssessment) -> RiskAssessment: ...
    async def find_by_order_id(self, order_id: str) -> RiskAssessment | None: ...
    async def mark_cancelled(self, order_id: str) -> str: ...


class VelocityCounterPort(Protocol):
    async def incr_and_count(self, customer_id: str, window_seconds: int) -> int: ...
    async def incr_sku_and_count(self, product_id: str, window_seconds: int) -> int: ...
    async def adjust(
        self, customer_id: str, delta: int, operation_id: str
    ) -> tuple[int, int, bool]: ...


class AssessmentCachePort(Protocol):
    async def get(self, order_id: str) -> RiskAssessment | None: ...
    async def put(self, assessment: RiskAssessment, ttl_seconds: int) -> None: ...


class CustomerHistoryPort(Protocol):
    async def fetch(self, customer_id: str) -> CustomerHistory: ...
