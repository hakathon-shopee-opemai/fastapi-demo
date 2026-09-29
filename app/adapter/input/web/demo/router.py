"""JWT-protected demo endpoints (rate limited), including the peer call."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.adapter.output.client.order.client import get_order_client
from app.common.ratelimit import rate_limit
from app.config.security.jwt import get_current_user

router = APIRouter(prefix="/api/v1/demo", tags=["demo"], dependencies=[Depends(rate_limit)])


@router.get("/whoami")
async def whoami(username: str = Depends(get_current_user)) -> dict:
    return {"username": username}


@router.get("/call-peer")
async def call_peer(
    message: str = "hi", username: str = Depends(get_current_user)
) -> dict:
    peer = await get_order_client().echo(message)
    return {"local": "risk-service", "peer": peer}
