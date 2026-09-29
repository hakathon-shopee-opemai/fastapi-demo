"""Use cases supporting the Order Cancellation Saga (risk-service peer side)."""
from __future__ import annotations

from app.adapter.output.cache.risk.velocity import AdjustResult
from app.application.risk.port.output.ports import (
    RiskAssessmentRepositoryPort,
    VelocityCounterPort,
)


class AdjustVelocityService:
    def __init__(self, velocity: VelocityCounterPort) -> None:
        self._velocity = velocity

    async def adjust(self, customer_id: str, delta: int, operation_id: str) -> AdjustResult:
        return await self._velocity.adjust(customer_id, delta, operation_id)


class CancelAssessmentService:
    def __init__(self, repository: RiskAssessmentRepositoryPort) -> None:
        self._repository = repository

    async def cancel(self, order_id: str) -> str:
        return await self._repository.mark_cancelled(order_id)
