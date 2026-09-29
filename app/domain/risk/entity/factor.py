"""A single risk rule that fired, with its point contribution (pure domain)."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.risk.vo.types import RiskFactorCode


@dataclass(frozen=True)
class RiskFactor:
    code: RiskFactorCode
    description: str
    weight: int
    contribution: int
