"""Risk value objects: enums + score helpers (pure domain)."""
from __future__ import annotations

from enum import StrEnum


class AccountStatus(StrEnum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class CustomerTier(StrEnum):
    STANDARD = "STANDARD"
    VIP = "VIP"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskDecision(StrEnum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class RiskFactorCode(StrEnum):
    ACCOUNT_BLOCKED = "ACCOUNT_BLOCKED"
    HIGH_VALUE = "HIGH_VALUE"
    VELOCITY = "VELOCITY"
    NEW_CUSTOMER = "NEW_CUSTOMER"
    DORMANT_REACTIVATION = "DORMANT_REACTIVATION"
    BULK_QUANTITY = "BULK_QUANTITY"
    VIP_DISCOUNT = "VIP_DISCOUNT"
    HISTORY_UNAVAILABLE = "HISTORY_UNAVAILABLE"


SCORE_MIN = 0
SCORE_MAX = 100


def clamp_score(value: int) -> int:
    return max(SCORE_MIN, min(SCORE_MAX, value))
