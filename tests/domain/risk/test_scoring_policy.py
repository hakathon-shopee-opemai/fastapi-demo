"""Truth-table tests for the deterministic ScoringPolicy (pure domain, no IO)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.domain.risk.service.scoring_policy import ScoringPolicy, decision_of, level_of
from app.domain.risk.vo.snapshot import CustomerHistory, OrderLineSnapshot, OrderSnapshot
from app.domain.risk.vo.types import AccountStatus, CustomerTier, RiskDecision, RiskFactorCode, RiskLevel

NOW = datetime(2026, 9, 29, tzinfo=UTC)


def _snapshot(total="100", qty=1):
    return OrderSnapshot(
        order_id="o-1",
        customer_id="c-1",
        total=Decimal(total),
        currency="USD",
        shipping_country="VN",
        lines=(OrderLineSnapshot("p-1", qty, Decimal("10")),),
    )


def _history(status=AccountStatus.ACTIVE, tier=CustomerTier.STANDARD, count=5, last=NOW, known=True):
    return CustomerHistory(status, tier, count, Decimal("1000"), "USD", last, known=known)


def _codes(factors):
    return {f.code for f in factors}


def test_established_small_order_is_low_approve():
    score, factors = ScoringPolicy.evaluate(_snapshot("100"), _history(), 0, NOW)
    assert score == 0
    assert level_of(score) is RiskLevel.LOW
    assert decision_of(level_of(score)) is RiskDecision.APPROVE
    assert factors == []


def test_new_customer_adds_20():
    score, factors = ScoringPolicy.evaluate(_snapshot("100"), _history(count=0), 0, NOW)
    assert score == 20
    assert RiskFactorCode.NEW_CUSTOMER in _codes(factors)


def test_high_value_tier1_and_tier2():
    s1, _ = ScoringPolicy.evaluate(_snapshot("6000"), _history(), 0, NOW)
    s2, _ = ScoringPolicy.evaluate(_snapshot("12000"), _history(), 0, NOW)
    assert s1 == 25
    assert s2 == 40


def test_velocity_thresholds():
    s3, _ = ScoringPolicy.evaluate(_snapshot("100"), _history(), 3, NOW)
    s6, _ = ScoringPolicy.evaluate(_snapshot("100"), _history(), 6, NOW)
    assert s3 == 30
    assert s6 == 50


def test_bulk_quantity_adds_10():
    score, factors = ScoringPolicy.evaluate(_snapshot("100", qty=11), _history(), 0, NOW)
    assert score == 10
    assert RiskFactorCode.BULK_QUANTITY in _codes(factors)


def test_dormant_reactivation():
    old = NOW - timedelta(days=200)
    score, factors = ScoringPolicy.evaluate(_snapshot("2500"), _history(last=old), 0, NOW)
    assert RiskFactorCode.DORMANT_REACTIVATION in _codes(factors)
    assert score == 15


def test_vip_discount_floors_at_zero():
    score, factors = ScoringPolicy.evaluate(_snapshot("100"), _history(tier=CustomerTier.VIP), 0, NOW)
    assert score == 0  # -15 floored to 0
    assert RiskFactorCode.VIP_DISCOUNT in _codes(factors)


def test_blocked_forces_reject():
    score, factors = ScoringPolicy.evaluate(_snapshot("100"), _history(status=AccountStatus.BLOCKED), 0, NOW)
    assert score == 100
    assert level_of(score) is RiskLevel.HIGH
    assert decision_of(level_of(score)) is RiskDecision.REJECT
    assert RiskFactorCode.ACCOUNT_BLOCKED in _codes(factors)


def test_combination_new_plus_high_value_is_medium_review():
    score, _ = ScoringPolicy.evaluate(_snapshot("6000"), _history(count=0), 0, NOW)
    assert score == 45  # 25 + 20
    assert level_of(score) is RiskLevel.MEDIUM
    assert decision_of(level_of(score)) is RiskDecision.REVIEW


def test_score_is_capped_at_100():
    score, _ = ScoringPolicy.evaluate(_snapshot("12000", qty=11), _history(status=AccountStatus.BLOCKED, count=0), 6, NOW)
    assert score == 100


def test_unknown_history_flags_and_treats_as_new():
    score, factors = ScoringPolicy.evaluate(_snapshot("100"), CustomerHistory.unknown(), 0, NOW)
    codes = _codes(factors)
    assert RiskFactorCode.HISTORY_UNAVAILABLE in codes
    assert RiskFactorCode.NEW_CUSTOMER in codes
    assert score == 20
