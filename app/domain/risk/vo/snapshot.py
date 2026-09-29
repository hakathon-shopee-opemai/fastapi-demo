"""Inputs to scoring: the order snapshot and the customer history (pure domain)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.risk.vo.types import AccountStatus, CustomerTier


@dataclass(frozen=True)
class OrderLineSnapshot:
    product_id: str
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class OrderSnapshot:
    order_id: str
    customer_id: str
    total: Decimal
    currency: str
    shipping_country: str | None
    lines: tuple[OrderLineSnapshot, ...]


@dataclass(frozen=True)
class CustomerHistory:
    account_status: AccountStatus
    tier: CustomerTier
    lifetime_order_count: int
    lifetime_gmv: Decimal
    currency: str
    last_order_at: datetime | None
    known: bool = True

    @classmethod
    def unknown(cls) -> "CustomerHistory":
        """Conservative fallback when the order-service history call fails."""
        return cls(AccountStatus.ACTIVE, CustomerTier.STANDARD, 0, Decimal("0"), "USD", None, known=False)
