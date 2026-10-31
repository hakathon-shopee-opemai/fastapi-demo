"""CustomerHistoryPort adapter: reverse hop to order-service with retry + safe fallback."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import httpx

from app.adapter.output.client.order.client import get_order_client
from app.common.resilience import retry
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
        try:
            return _map(await self._get(customer_id))
        except (httpx.HTTPError, KeyError, ValueError):
            return CustomerHistory.unknown()

    @retry(attempts=3, backoff_seconds=0.1, on=(httpx.HTTPError,))
    async def _get(self, customer_id: str) -> dict:
        return await get_order_client().get_order_history(customer_id)
