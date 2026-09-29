"""RiskAssessment aggregate root (pure domain)."""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.risk.entity.factor import RiskFactor
from app.domain.risk.service.scoring_policy import ScoringPolicy, decision_of, level_of
from app.domain.risk.vo.snapshot import CustomerHistory, OrderSnapshot
from app.domain.risk.vo.types import RiskDecision, RiskLevel


def _fingerprint(snapshot: OrderSnapshot) -> str:
    parts = [snapshot.order_id, str(snapshot.total), snapshot.currency]
    parts += [f"{ln.product_id}:{ln.quantity}:{ln.unit_price}" for ln in snapshot.lines]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


@dataclass(frozen=True)
class RiskAssessment:
    id: uuid.UUID
    order_id: str
    customer_id: str
    score: int
    level: RiskLevel
    decision: RiskDecision
    factors: tuple[RiskFactor, ...]
    assessed_at: datetime
    fingerprint: str

    @classmethod
    def evaluate(
        cls,
        snapshot: OrderSnapshot,
        history: CustomerHistory,
        velocity_count: int,
        now: datetime,
        assessment_id: uuid.UUID | None = None,
    ) -> "RiskAssessment":
        score, factors = ScoringPolicy.evaluate(snapshot, history, velocity_count, now)
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
            fingerprint=_fingerprint(snapshot),
        )
