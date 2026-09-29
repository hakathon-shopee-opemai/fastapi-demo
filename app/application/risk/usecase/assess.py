"""AssessOrderRisk use case: orchestrates velocity, history hop, scoring, persistence."""
from __future__ import annotations

from datetime import UTC, datetime

from app.application.risk.dto.commands import AssessOrderRiskCommand
from app.application.risk.port.output.ports import (
    AssessmentCachePort,
    CustomerHistoryPort,
    RiskAssessmentRepositoryPort,
    VelocityCounterPort,
)
from app.domain.risk.aggregate.assessment import RiskAssessment
from app.domain.risk.vo.snapshot import OrderSnapshot

VELOCITY_WINDOW_SECONDS = 3600
ASSESSMENT_TTL_SECONDS = 600


class AssessOrderRiskService:
    def __init__(
        self,
        repository: RiskAssessmentRepositoryPort,
        cache: AssessmentCachePort,
        velocity: VelocityCounterPort,
        history: CustomerHistoryPort,
    ) -> None:
        self._repo = repository
        self._cache = cache
        self._velocity = velocity
        self._history = history

    async def assess(self, command: AssessOrderRiskCommand) -> RiskAssessment:
        cached = await self._cache.get(command.order_id)
        if cached is not None:
            return cached

        velocity_count = await self._velocity.incr_and_count(command.customer_id, VELOCITY_WINDOW_SECONDS)
        history = await self._history.fetch(command.customer_id)

        snapshot = OrderSnapshot(
            order_id=command.order_id,
            customer_id=command.customer_id,
            total=command.total,
            currency=command.currency,
            shipping_country=command.shipping_country,
            lines=tuple(command.lines),
        )
        assessment = RiskAssessment.evaluate(snapshot, history, velocity_count, datetime.now(UTC))

        await self._repo.save(assessment)
        await self._cache.put(assessment, ASSESSMENT_TTL_SECONDS)
        return assessment
