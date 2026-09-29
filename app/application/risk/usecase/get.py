"""GetAssessment query use case."""
from __future__ import annotations

from app.application.risk.port.output.ports import RiskAssessmentRepositoryPort
from app.domain.risk.aggregate.assessment import RiskAssessment


class GetAssessmentService:
    def __init__(self, repository: RiskAssessmentRepositoryPort) -> None:
        self._repo = repository

    async def get(self, order_id: str) -> RiskAssessment | None:
        return await self._repo.find_by_order_id(order_id)
