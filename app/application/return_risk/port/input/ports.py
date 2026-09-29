"""Inbound ports (driving side / use cases) for the return-risk context."""
from __future__ import annotations

from typing import Protocol

from app.application.return_risk.dto.commands import AssessReturnRiskCommand
from app.domain.return_risk.aggregate.assessment import ReturnRiskAssessment


class AssessReturnRiskUseCase(Protocol):
    async def assess(self, command: AssessReturnRiskCommand) -> ReturnRiskAssessment: ...
