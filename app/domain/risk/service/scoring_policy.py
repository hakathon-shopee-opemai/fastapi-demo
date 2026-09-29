"""ScoringPolicy — the deterministic fraud-risk rule engine (pure domain).

Single source of truth for thresholds/weights (see docs/01 section 6).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.domain.risk.entity.factor import RiskFactor
from app.domain.risk.vo.snapshot import CustomerHistory, OrderSnapshot
from app.domain.risk.vo.types import (
    AccountStatus,
    CustomerTier,
    RiskDecision,
    RiskFactorCode,
    RiskLevel,
    clamp_score,
)

HIGH_VALUE_T1 = Decimal("5000")
HIGH_VALUE_T2 = Decimal("10000")
DORMANT_DAYS = 180
DORMANT_MIN_TOTAL = Decimal("2000")
BULK_QTY = 10


def level_of(score: int) -> RiskLevel:
    if score < 40:
        return RiskLevel.LOW
    if score < 70:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


def decision_of(level: RiskLevel) -> RiskDecision:
    return {
        RiskLevel.LOW: RiskDecision.APPROVE,
        RiskLevel.MEDIUM: RiskDecision.REVIEW,
        RiskLevel.HIGH: RiskDecision.REJECT,
    }[level]


class ScoringPolicy:
    """Evaluate an order snapshot + customer history + velocity into (score, factors)."""

    @staticmethod
    def evaluate(
        snapshot: OrderSnapshot,
        history: CustomerHistory,
        velocity_count: int,
        now: datetime,
    ) -> tuple[int, list[RiskFactor]]:
        factors: list[RiskFactor] = []
        score = 0

        if not history.known:
            factors.append(
                RiskFactor(
                    RiskFactorCode.HISTORY_UNAVAILABLE,
                    "Customer history unavailable; scored conservatively",
                    0,
                    0,
                )
            )

        if history.account_status == AccountStatus.BLOCKED:
            factors.append(RiskFactor(RiskFactorCode.ACCOUNT_BLOCKED, "Customer account is blocked", 100, 100))
            score += 100

        high_value = 40 if snapshot.total > HIGH_VALUE_T2 else 25 if snapshot.total > HIGH_VALUE_T1 else 0
        if high_value:
            factors.append(
                RiskFactor(RiskFactorCode.HIGH_VALUE, f"Order total {snapshot.total} above threshold", high_value, high_value)
            )
            score += high_value

        velocity = 50 if velocity_count >= 6 else 30 if velocity_count >= 3 else 0
        if velocity:
            factors.append(
                RiskFactor(RiskFactorCode.VELOCITY, f"{velocity_count} orders in the last hour", velocity, velocity)
            )
            score += velocity

        if history.lifetime_order_count == 0:
            factors.append(RiskFactor(RiskFactorCode.NEW_CUSTOMER, "First-ever order for this customer", 20, 20))
            score += 20

        if (
            history.last_order_at is not None
            and (now - history.last_order_at) > timedelta(days=DORMANT_DAYS)
            and snapshot.total > DORMANT_MIN_TOTAL
        ):
            factors.append(RiskFactor(RiskFactorCode.DORMANT_REACTIVATION, "Large order after long dormancy", 15, 15))
            score += 15

        if any(line.quantity > BULK_QTY for line in snapshot.lines):
            factors.append(RiskFactor(RiskFactorCode.BULK_QUANTITY, "A line exceeds the bulk quantity threshold", 10, 10))
            score += 10

        if history.tier == CustomerTier.VIP:
            factors.append(RiskFactor(RiskFactorCode.VIP_DISCOUNT, "Trusted VIP customer", -15, -15))
            score -= 15

        return clamp_score(score), factors
