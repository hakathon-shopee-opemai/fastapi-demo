"""ReturnRiskAssessment aggregate root (pure domain)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.return_risk.entity.factor import ReturnRiskFactor
from app.domain.return_risk.service.scoring_policy import (
    ReturnScoringPolicy,
    decision_of,
    level_of,
)
from app.domain.return_risk.vo.snapshot import ReturnHistory, ReturnSnapshot
from app.domain.return_risk.vo.types import ReturnDecision, ReturnLevel


@dataclass(frozen=True)
class ReturnRiskAssessment:
    id: uuid.UUID
    order_id: str
    customer_id: str
    score: int
    level: ReturnLevel
    decision: ReturnDecision
    factors: tuple[ReturnRiskFactor, ...]
    assessed_at: datetime

    @classmethod
    def evaluate(
        cls,
        snapshot: ReturnSnapshot,
        history: ReturnHistory,
        velocity_count: int,
        now: datetime,
        assessment_id: uuid.UUID | None = None,
    ) -> ReturnRiskAssessment:
        score, factors = ReturnScoringPolicy.evaluate(snapshot, history, velocity_count, now)
        level = level_of(score)
        return cls(
            id=assessment_id or uuid.uuid4(),
            order_id=snapshot.order_id,
            customer_id=snapshot.customer_id,
            score=score,
            level=level,
            decision=decision_of(level),
            factors=tuple(factors),
            assessed_at=now,
        )
