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
# a SKU ordered this many times per hour counts like one extra in-flight order of the customer
SKU_VELOCITY_PER_ORDER = 25


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
        # idempotency: the persisted assessment is the source of truth (cache is write-through)
        existing = await self._repo.find_by_order_id(command.order_id)
        if existing is not None:
            return existing

        velocity_count = await self._velocity.incr_and_count(command.customer_id, VELOCITY_WINDOW_SECONDS)
        for line in command.lines:
            sku_count = await self._velocity.incr_sku_and_count(
                line.product_id, VELOCITY_WINDOW_SECONDS
            )
            if sku_count >= SKU_VELOCITY_PER_ORDER:
                velocity_count += sku_count // SKU_VELOCITY_PER_ORDER
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
