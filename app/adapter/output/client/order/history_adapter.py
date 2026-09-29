"""CustomerHistoryPort adapter: reverse hop to order-service with 1 retry + safe fallback."""
from __future__ import annotations

import asyncio
import random
from datetime import datetime
from decimal import Decimal

from app.adapter.output.client.order.client import get_order_client
from app.domain.risk.vo.snapshot import CustomerHistory
from app.domain.risk.vo.types import AccountStatus, CustomerTier


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _map(data: dict) -> CustomerHistory:
    return CustomerHistory(
        account_status=AccountStatus(data["accountStatus"]),
        tier=CustomerTier(data["tier"]),
        lifetime_order_count=int(data["lifetimeOrderCount"]),
        lifetime_gmv=Decimal(str(data["lifetimeGmv"])),
        currency=data.get("currency", "USD"),
        last_order_at=_parse_dt(data.get("lastOrderAt")),
        known=True,
    )


class HttpCustomerHistoryAdapter:
    """Never fails the assessment: on error returns CustomerHistory.unknown()."""

    async def fetch(self, customer_id: str) -> CustomerHistory:
        for attempt in range(2):
            try:
                return _map(await get_order_client().get_order_history(customer_id))
            except Exception:  # noqa: BLE001 - fall back conservatively, one retry
                if attempt == 0:
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                    continue
                return CustomerHistory.unknown()
        return CustomerHistory.unknown()
