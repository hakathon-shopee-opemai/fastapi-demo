"""Application commands for the return-risk context."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.return_risk.vo.types import CustomerTier, ReturnReason


@dataclass(frozen=True)
class AssessReturnRiskCommand:
    order_id: str
    customer_id: str
    order_total: Decimal
    requested_amount: Decimal
    currency: str
    reason: ReturnReason
    tier: CustomerTier
    days_since_order: int
