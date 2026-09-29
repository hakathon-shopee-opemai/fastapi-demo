"""Truth-table tests for the deterministic ReturnScoringPolicy (pure domain, no IO)."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.return_risk.service.scoring_policy import (
    ReturnScoringPolicy,
    decision_of,
    level_of,
)
from app.domain.return_risk.vo.snapshot import ReturnHistory, ReturnSnapshot
from app.domain.return_risk.vo.types import (
    CustomerTier,
    ReturnDecision,
    ReturnFactorCode,
    ReturnLevel,
    ReturnReason,
    clamp_score,
)

NOW = datetime(2026, 9, 29, tzinfo=UTC)


def _snapshot(
    order_total="100",
    requested="100",
    reason=ReturnReason.DEFECTIVE,
    tier=CustomerTier.STANDARD,
    days_since_order=1,
):
    return ReturnSnapshot(
        order_id="o-1",
        customer_id="c-1",
        order_total=Decimal(order_total),
        requested_amount=Decimal(requested),
        currency="USD",
        reason=reason,
        tier=tier,
        days_since_order=days_since_order,
    )


def _history(rate=0.0, returns_30d=0, known=True):
    return ReturnHistory(
        total_orders=20,
        total_returns=int(rate * 20),
        return_rate=rate,
        total_returned_amount=Decimal("0"),
        currency="USD",
        returns_last_30_days=returns_30d,
        last_return_at=None,
        known=known,
    )


def _codes(factors):
    return {f.code for f in factors}


# --- baseline ---------------------------------------------------------------


def test_clean_return_is_low_auto_refund():
    score, factors = ReturnScoringPolicy.evaluate(_snapshot(), _history(), 0, NOW)
    assert score == 0
    assert factors == []
    assert level_of(score) is ReturnLevel.LOW
    assert decision_of(level_of(score)) is ReturnDecision.AUTO_REFUND


# --- HIGH_RETURN_RATE tiers -------------------------------------------------


def test_high_return_rate_tiers():
    s1, f1 = ReturnScoringPolicy.evaluate(_snapshot(), _history(rate=0.2), 0, NOW)
    s2, _ = ReturnScoringPolicy.evaluate(_snapshot(), _history(rate=0.4), 0, NOW)
    s3, _ = ReturnScoringPolicy.evaluate(_snapshot(), _history(rate=0.6), 0, NOW)
    assert (s1, s2, s3) == (10, 25, 40)
    assert ReturnFactorCode.HIGH_RETURN_RATE in _codes(f1)


def test_return_rate_at_lowest_threshold_is_zero():
    score, _ = ReturnScoringPolicy.evaluate(_snapshot(), _history(rate=0.15), 0, NOW)
    assert score == 0  # strictly > 0.15 required


# --- RETURN_VELOCITY (returns in last 30 days) ------------------------------


def test_return_velocity_tiers():
    s_low, _ = ReturnScoringPolicy.evaluate(_snapshot(), _history(returns_30d=2), 0, NOW)
    s3, f3 = ReturnScoringPolicy.evaluate(_snapshot(), _history(returns_30d=3), 0, NOW)
    s5, _ = ReturnScoringPolicy.evaluate(_snapshot(), _history(returns_30d=5), 0, NOW)
    assert (s_low, s3, s5) == (0, 10, 25)
    assert ReturnFactorCode.RETURN_VELOCITY in _codes(f3)


# --- ASSESS_BURST (redis velocity) ------------------------------------------


def test_assess_burst_tiers():
    s2, _ = ReturnScoringPolicy.evaluate(_snapshot(), _history(), 2, NOW)
    s3, f3 = ReturnScoringPolicy.evaluate(_snapshot(), _history(), 3, NOW)
    s5, _ = ReturnScoringPolicy.evaluate(_snapshot(), _history(), 5, NOW)
    assert (s2, s3, s5) == (0, 5, 15)
    assert ReturnFactorCode.ASSESS_BURST in _codes(f3)


# --- HIGH_VALUE_REFUND ------------------------------------------------------


def test_high_value_refund_tiers():
    s500, _ = ReturnScoringPolicy.evaluate(_snapshot(requested="500"), _history(), 0, NOW)
    s501, f501 = ReturnScoringPolicy.evaluate(_snapshot(requested="501"), _history(), 0, NOW)
    s1001, _ = ReturnScoringPolicy.evaluate(_snapshot(requested="1001"), _history(), 0, NOW)
    assert (s500, s501, s1001) == (0, 5, 15)
    assert ReturnFactorCode.HIGH_VALUE_REFUND in _codes(f501)


# --- RISKY_REASON -----------------------------------------------------------


def test_risky_reason_tiers():
    s_ok, f_ok = ReturnScoringPolicy.evaluate(
        _snapshot(reason=ReturnReason.DEFECTIVE), _history(), 0, NOW
    )
    s_nad, _ = ReturnScoringPolicy.evaluate(
        _snapshot(reason=ReturnReason.NOT_AS_DESCRIBED), _history(), 0, NOW
    )
    s_inr, f_inr = ReturnScoringPolicy.evaluate(
        _snapshot(reason=ReturnReason.ITEM_NOT_RECEIVED), _history(), 0, NOW
    )
    assert (s_ok, s_nad, s_inr) == (0, 5, 20)
    assert ReturnFactorCode.RISKY_REASON not in _codes(f_ok)
    assert ReturnFactorCode.RISKY_REASON in _codes(f_inr)


# --- LATE_RETURN ------------------------------------------------------------


def test_late_return():
    s25, _ = ReturnScoringPolicy.evaluate(_snapshot(days_since_order=25), _history(), 0, NOW)
    s26, f26 = ReturnScoringPolicy.evaluate(_snapshot(days_since_order=26), _history(), 0, NOW)
    assert (s25, s26) == (0, 10)
    assert ReturnFactorCode.LATE_RETURN in _codes(f26)


# --- BLOCKED / VIP ----------------------------------------------------------


def test_blocked_customer_dominates_and_denies():
    score, factors = ReturnScoringPolicy.evaluate(
        _snapshot(tier=CustomerTier.BLOCKED), _history(rate=0.6, returns_30d=5), 5, NOW
    )
    assert score == 100
    assert level_of(score) is ReturnLevel.HIGH
    assert decision_of(level_of(score)) is ReturnDecision.DENY
    assert ReturnFactorCode.BLOCKED_CUSTOMER in _codes(factors)


def test_vip_trusted_min_clamped_at_zero():
    score, factors = ReturnScoringPolicy.evaluate(
        _snapshot(tier=CustomerTier.VIP), _history(), 0, NOW
    )
    assert score == 0  # -10 floored to 0
    assert ReturnFactorCode.TRUSTED_CUSTOMER in _codes(factors)


def test_vip_discount_offsets_positive_factors():
    # rate 0.2 (+10) with VIP (-10) nets to 0.
    score, _ = ReturnScoringPolicy.evaluate(
        _snapshot(tier=CustomerTier.VIP), _history(rate=0.2), 0, NOW
    )
    assert score == 0


# --- buckets ----------------------------------------------------------------


def test_medium_bucket_is_review():
    score, _ = ReturnScoringPolicy.evaluate(_snapshot(), _history(rate=0.6), 0, NOW)  # 40
    assert level_of(score) is ReturnLevel.MEDIUM
    assert decision_of(level_of(score)) is ReturnDecision.REVIEW


def test_high_bucket_is_deny_by_accumulation():
    # 40 + 25 + 20 = 85 without a blocked tier.
    score, _ = ReturnScoringPolicy.evaluate(
        _snapshot(reason=ReturnReason.ITEM_NOT_RECEIVED),
        _history(rate=0.6, returns_30d=5),
        0,
        NOW,
    )
    assert score == 85
    assert level_of(score) is ReturnLevel.HIGH
    assert decision_of(level_of(score)) is ReturnDecision.DENY


def test_bucket_boundaries():
    assert level_of(29) is ReturnLevel.LOW
    assert level_of(30) is ReturnLevel.MEDIUM
    assert level_of(69) is ReturnLevel.MEDIUM
    assert level_of(70) is ReturnLevel.HIGH


# --- clamp bounds -----------------------------------------------------------


def test_clamp_score_bounds():
    assert clamp_score(-50) == 0
    assert clamp_score(0) == 0
    assert clamp_score(100) == 100
    assert clamp_score(250) == 100


def test_score_capped_at_100_when_everything_fires():
    score, _ = ReturnScoringPolicy.evaluate(
        _snapshot(requested="5000", reason=ReturnReason.ITEM_NOT_RECEIVED, days_since_order=40),
        _history(rate=0.9, returns_30d=9),
        9,
        NOW,
    )
    assert score == 100
