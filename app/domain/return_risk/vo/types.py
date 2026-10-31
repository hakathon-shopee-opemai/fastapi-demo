"""Return-risk value objects: enums + score helpers (pure domain)."""
from __future__ import annotations

from enum import StrEnum


class ReturnReason(StrEnum):
    DEFECTIVE = "DEFECTIVE"
    NOT_AS_DESCRIBED = "NOT_AS_DESCRIBED"
    NO_LONGER_NEEDED = "NO_LONGER_NEEDED"
    ITEM_NOT_RECEIVED = "ITEM_NOT_RECEIVED"
    WRONG_ITEM = "WRONG_ITEM"
    OTHER = "OTHER"


class CustomerTier(StrEnum):
    STANDARD = "STANDARD"
    VIP = "VIP"
    BLOCKED = "BLOCKED"


class ReturnLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReturnDecision(StrEnum):
    AUTO_REFUND = "AUTO_REFUND"
    REVIEW = "REVIEW"
    DENY = "DENY"


class ReturnFactorCode(StrEnum):
    HIGH_RETURN_RATE = "HIGH_RETURN_RATE"
    RETURN_VELOCITY = "RETURN_VELOCITY"
    ASSESS_BURST = "ASSESS_BURST"
    HIGH_VALUE_REFUND = "HIGH_VALUE_REFUND"
    RISKY_REASON = "RISKY_REASON"
    LATE_RETURN = "LATE_RETURN"
    BLOCKED_CUSTOMER = "BLOCKED_CUSTOMER"
    TRUSTED_CUSTOMER = "TRUSTED_CUSTOMER"


SCORE_MIN = 0
SCORE_MAX = 100


def clamp_score(value: int) -> int:
    return max(SCORE_MIN, min(SCORE_MAX, value))
