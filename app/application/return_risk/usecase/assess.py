"""AssessReturnRisk use case: orchestrates velocity, history hop, scoring, persistence."""
from __future__ import annotations

from datetime import UTC, datetime

from app.application.return_risk.dto.commands import AssessReturnRiskCommand
from app.application.return_risk.port.output.ports import (
    CustomerReturnHistoryPort,
    ReturnDecisionCachePort,
    ReturnRiskRepositoryPort,
    ReturnVelocityCounterPort,
)
from app.domain.return_risk.aggregate.assessment import ReturnRiskAssessment
from app.domain.return_risk.vo.snapshot import ReturnSnapshot

RETURN_VELOCITY_WINDOW_SECONDS = 3600
RETURN_DECISION_TTL_SECONDS = 600


class ReturnRiskService:
    def __init__(
        self,
        repository: ReturnRiskRepositoryPort,
        cache: ReturnDecisionCachePort,
        velocity: ReturnVelocityCounterPort,
        history: CustomerReturnHistoryPort,
    ) -> None:
        self._repo = repository
        self._cache = cache
        self._velocity = velocity
        self._history = history

    async def assess(self, command: AssessReturnRiskCommand) -> ReturnRiskAssessment:
        cached = await self._cache.get(command.order_id)
        if cached is not None:
            return cached

        velocity_count = await self._velocity.incr_and_count(
            command.customer_id, RETURN_VELOCITY_WINDOW_SECONDS
        )
        history = await self._history.fetch(command.customer_id)

        snapshot = ReturnSnapshot(
            order_id=command.order_id,
            customer_id=command.customer_id,
            order_total=command.order_total,
            requested_amount=command.requested_amount,
            currency=command.currency,
            reason=command.reason,
            tier=command.tier,
            days_since_order=command.days_since_order,
        )
        assessment = ReturnRiskAssessment.evaluate(
            snapshot, history, velocity_count, datetime.now(UTC)
        )

        await self._repo.save(assessment)
        await self._cache.put(assessment, RETURN_DECISION_TTL_SECONDS)
        return assessment
