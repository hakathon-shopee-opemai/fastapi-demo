"""Tests for the return-history client mapper + conservative fail-safe fallback."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.adapter.output.client.order import return_history_adapter
from app.adapter.output.client.order.return_history_adapter import (
    HttpCustomerReturnHistoryAdapter,
    _map,
)


def test_map_parses_camelcase_payload():
    history = _map(
        {
            "customerId": "c-1",
            "totalOrders": 20,
            "totalReturns": 5,
            "returnRate": 0.25,
            "totalReturnedAmount": 480.00,
            "currency": "USD",
            "returnsLast30Days": 3,
            "lastReturnAt": "2026-09-20T10:00:00+00:00",
        }
    )
    assert history.total_orders == 20
    assert history.total_returns == 5
    assert history.return_rate == 0.25
    assert history.total_returned_amount == Decimal("480.0")
    assert history.returns_last_30_days == 3
    assert history.last_return_at == datetime.fromisoformat("2026-09-20T10:00:00+00:00")
    assert history.known is True


def test_map_handles_null_last_return_at():
    history = _map(
        {
            "customerId": "c-1",
            "totalOrders": 0,
            "totalReturns": 0,
            "returnRate": 0.0,
            "totalReturnedAmount": 0,
            "currency": "USD",
            "returnsLast30Days": 0,
            "lastReturnAt": None,
        }
    )
    assert history.last_return_at is None
    assert history.return_rate == 0.0


class _FailingClient:
    async def get_return_history(self, customer_id: str) -> dict:
        raise RuntimeError("order-service down")


async def test_fetch_falls_back_to_unknown_on_error(monkeypatch):
    monkeypatch.setattr(return_history_adapter, "get_order_client", lambda: _FailingClient())
    # Skip the retry backoff sleep to keep the test fast.
    monkeypatch.setattr(return_history_adapter.asyncio, "sleep", _noop_sleep)

    history = await HttpCustomerReturnHistoryAdapter().fetch("c-1")

    assert history.known is False
    assert history.total_orders == 0
    assert history.total_returns == 0
    assert history.return_rate == 0.0
    assert history.returns_last_30_days == 0
    assert history.last_return_at is None


class _OkClient:
    def __init__(self) -> None:
        self.calls = 0

    async def get_return_history(self, customer_id: str) -> dict:
        self.calls += 1
        return {
            "customerId": customer_id,
            "totalOrders": 10,
            "totalReturns": 2,
            "returnRate": 0.2,
            "totalReturnedAmount": 50,
            "currency": "USD",
            "returnsLast30Days": 1,
            "lastReturnAt": None,
        }


async def test_fetch_maps_successful_response(monkeypatch):
    client = _OkClient()
    monkeypatch.setattr(return_history_adapter, "get_order_client", lambda: client)

    history = await HttpCustomerReturnHistoryAdapter().fetch("c-1")

    assert client.calls == 1
    assert history.known is True
    assert history.return_rate == 0.2


async def _noop_sleep(_seconds: float) -> None:
    return None
