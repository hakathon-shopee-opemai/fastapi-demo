"""CustomerReturnHistoryPort adapter: reverse hop to order-service with 1 retry + safe fallback."""
from __future__ import annotations

import asyncio
import random
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.adapter.output.client.order.client import get_order_client
from app.domain.return_risk.vo.snapshot import ReturnHistory


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _map(data: dict[str, Any]) -> ReturnHistory:
    return ReturnHistory(
        total_orders=int(data["totalOrders"]),
        total_returns=int(data["totalReturns"]),
        return_rate=float(data["returnRate"]),
        total_returned_amount=Decimal(str(data["totalReturnedAmount"])),
        currency=data.get("currency", "USD"),
        returns_last_30_days=int(data["returnsLast30Days"]),
        last_return_at=_parse_dt(data.get("lastReturnAt")),
        known=True,
    )


class HttpCustomerReturnHistoryAdapter:
    """Never fails the assessment: on error returns ReturnHistory.unknown()."""

    async def fetch(self, customer_id: str) -> ReturnHistory:
        for attempt in range(2):
            try:
                return _map(await get_order_client().get_return_history(customer_id))
            except Exception:  # noqa: BLE001 - fall back conservatively, one retry
                if attempt == 0:
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                    continue
                return ReturnHistory.unknown()
        return ReturnHistory.unknown()
