"""Inputs to return-fraud scoring: the return snapshot and the return history (pure domain)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.return_risk.vo.types import CustomerTier, ReturnReason


@dataclass(frozen=True)
class ReturnSnapshot:
    order_id: str
    customer_id: str
    order_total: Decimal
    requested_amount: Decimal
    currency: str
    reason: ReturnReason
    tier: CustomerTier
    days_since_order: int


@dataclass(frozen=True)
class ReturnHistory:
    total_orders: int
    total_returns: int
    return_rate: float
    total_returned_amount: Decimal
    currency: str
    returns_last_30_days: int
    last_return_at: datetime | None
    known: bool = True

    @classmethod
    def unknown(cls) -> ReturnHistory:
        """Conservative fallback when the order-service return-history call fails."""
        return cls(0, 0, 0.0, Decimal("0"), "USD", 0, None, known=False)
