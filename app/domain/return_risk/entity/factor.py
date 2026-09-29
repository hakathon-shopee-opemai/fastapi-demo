"""A single return-fraud rule that fired, with its point contribution (pure domain)."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.return_risk.vo.types import ReturnFactorCode


@dataclass(frozen=True)
class ReturnRiskFactor:
    code: ReturnFactorCode
    description: str
    weight: int
    contribution: int
