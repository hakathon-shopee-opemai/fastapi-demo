"""Application commands/queries for the risk context."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.risk.vo.snapshot import OrderLineSnapshot


@dataclass(frozen=True)
class AssessOrderRiskCommand:
    order_id: str
    customer_id: str
    total: Decimal
    currency: str
    shipping_country: str | None
    lines: tuple[OrderLineSnapshot, ...]
