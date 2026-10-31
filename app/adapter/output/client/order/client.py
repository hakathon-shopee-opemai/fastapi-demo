"""Signed httpx client to the peer order-service (the reverse parallax hop)."""
from __future__ import annotations

import time
from typing import Any

import httpx

from app.common.logging.context import TRACE_HEADER, get_trace_id
from app.config.security.hmac import SIGNATURE_HEADER, TIMESTAMP_HEADER, sign
from app.config.settings.settings import get_settings

_client: httpx.AsyncClient | None = None


def init_order_client() -> None:
    global _client
    settings = get_settings()
    timeout = httpx.Timeout(
        connect=settings.peer_connect_timeout_seconds,
        read=settings.peer_read_timeout_seconds,
        write=settings.peer_read_timeout_seconds,
        pool=settings.peer_connect_timeout_seconds,
    )
    _client = httpx.AsyncClient(base_url=settings.order_service_base_url, timeout=timeout)


async def close_order_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
    _client = None


def get_order_client() -> OrderServiceClient:
    if _client is None:
        raise RuntimeError("Order client not initialized; call init_order_client() first.")
    return OrderServiceClient(_client)


class OrderServiceClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_order_history(self, customer_id: str) -> dict:
        """Reverse parallax hop: GET the customer's committed order history (HMAC-signed)."""
        path = f"/internal/customers/{customer_id}/order-history"
        ts = str(int(time.time()))
        headers = {
            TRACE_HEADER: get_trace_id(),
            TIMESTAMP_HEADER: ts,
            SIGNATURE_HEADER: sign("GET", path, ts, b""),
        }
        resp = await self._client.get(path, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def get_return_history(self, customer_id: str) -> dict[str, Any]:
        """Reverse parallax hop: GET the customer's return history (HMAC-signed)."""
        path = f"/internal/customers/{customer_id}/return-history"
        ts = str(int(time.time()))
        headers = {
            TRACE_HEADER: get_trace_id(),
            TIMESTAMP_HEADER: ts,
            SIGNATURE_HEADER: sign("GET", path, ts, b""),
        }
        resp = await self._client.get(path, headers=headers)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data
