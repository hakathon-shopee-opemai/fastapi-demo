"""Inbound ports (driving side / use cases) for the risk context."""
from __future__ import annotations

from typing import Protocol

from app.application.risk.dto.commands import AssessOrderRiskCommand
from app.domain.risk.aggregate.assessment import RiskAssessment


class AssessOrderRiskUseCase(Protocol):
    async def assess(self, command: AssessOrderRiskCommand) -> RiskAssessment: ...


class GetAssessmentUseCase(Protocol):
    async def get(self, order_id: str) -> RiskAssessment | None: ...
