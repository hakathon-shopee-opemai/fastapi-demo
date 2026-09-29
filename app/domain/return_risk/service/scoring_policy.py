"""ReturnScoringPolicy — the deterministic return-fraud rule engine (pure domain).

Single source of truth for thresholds/weights/buckets (see docs/06 section 1).
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.domain.return_risk.entity.factor import ReturnRiskFactor
from app.domain.return_risk.vo.snapshot import ReturnHistory, ReturnSnapshot
from app.domain.return_risk.vo.types import (
    CustomerTier,
    ReturnDecision,
    ReturnFactorCode,
    ReturnLevel,
    ReturnReason,
    clamp_score,
)

RETURN_RATE_T1 = 0.15
RETURN_RATE_T2 = 0.3
RETURN_RATE_T3 = 0.5
HIGH_VALUE_T1 = Decimal("500")
HIGH_VALUE_T2 = Decimal("1000")
LATE_RETURN_DAYS = 25


def level_of(score: int) -> ReturnLevel:
    if score < 30:
        return ReturnLevel.LOW
    if score < 70:
        return ReturnLevel.MEDIUM
    return ReturnLevel.HIGH


def decision_of(level: ReturnLevel) -> ReturnDecision:
    return {
        ReturnLevel.LOW: ReturnDecision.AUTO_REFUND,
        ReturnLevel.MEDIUM: ReturnDecision.REVIEW,
        ReturnLevel.HIGH: ReturnDecision.DENY,
    }[level]


class ReturnScoringPolicy:
    """Evaluate a return snapshot + return history + assess-velocity into (score, factors)."""

    @staticmethod
    def evaluate(
        snapshot: ReturnSnapshot,
        history: ReturnHistory,
        velocity_count: int,
        now: datetime,
    ) -> tuple[int, list[ReturnRiskFactor]]:
        factors: list[ReturnRiskFactor] = []
        score = 0

        if snapshot.tier == CustomerTier.BLOCKED:
            factors.append(
                ReturnRiskFactor(ReturnFactorCode.BLOCKED_CUSTOMER, "Customer is blocked", 100, 100)
            )
            score += 100

        rate = (
            40 if history.return_rate > RETURN_RATE_T3
            else 25 if history.return_rate > RETURN_RATE_T2
            else 10 if history.return_rate > RETURN_RATE_T1
            else 0
        )
        if rate:
            factors.append(
                ReturnRiskFactor(
                    ReturnFactorCode.HIGH_RETURN_RATE,
                    f"Return rate {history.return_rate:.2f} above threshold",
                    rate,
                    rate,
                )
            )
            score += rate

        recent_returns = history.returns_last_30_days
        recent = 25 if recent_returns >= 5 else 10 if recent_returns >= 3 else 0
        if recent:
            factors.append(
                ReturnRiskFactor(
                    ReturnFactorCode.RETURN_VELOCITY,
                    f"{history.returns_last_30_days} returns in the last 30 days",
                    recent,
                    recent,
                )
            )
            score += recent

        burst = 15 if velocity_count >= 5 else 5 if velocity_count >= 3 else 0
        if burst:
            factors.append(
                ReturnRiskFactor(
                    ReturnFactorCode.ASSESS_BURST,
                    f"{velocity_count} return assessments in the last hour",
                    burst,
                    burst,
                )
            )
            score += burst

        high_value = (
            15 if snapshot.requested_amount > HIGH_VALUE_T2
            else 5 if snapshot.requested_amount > HIGH_VALUE_T1
            else 0
        )
        if high_value:
            factors.append(
                ReturnRiskFactor(
                    ReturnFactorCode.HIGH_VALUE_REFUND,
                    f"Requested refund {snapshot.requested_amount} above threshold",
                    high_value,
                    high_value,
                )
            )
            score += high_value

        risky_reason = (
            20 if snapshot.reason == ReturnReason.ITEM_NOT_RECEIVED
            else 5 if snapshot.reason == ReturnReason.NOT_AS_DESCRIBED
            else 0
        )
        if risky_reason:
            factors.append(
                ReturnRiskFactor(
                    ReturnFactorCode.RISKY_REASON,
                    f"reason={snapshot.reason}",
                    risky_reason,
                    risky_reason,
                )
            )
            score += risky_reason

        if snapshot.days_since_order > LATE_RETURN_DAYS:
            factors.append(
                ReturnRiskFactor(
                    ReturnFactorCode.LATE_RETURN,
                    f"Return requested {snapshot.days_since_order} days after order",
                    10,
                    10,
                )
            )
            score += 10

        if snapshot.tier == CustomerTier.VIP:
            factors.append(
                ReturnRiskFactor(
                    ReturnFactorCode.TRUSTED_CUSTOMER, "Trusted VIP customer", -10, -10
                )
            )
            score -= 10

        return clamp_score(score), factors
