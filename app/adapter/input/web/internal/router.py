"""Internal HMAC-protected echo endpoint (exercises the parallax hop)."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.common.logging.context import get_trace_id
from app.config.security.hmac import require_service_signature

router = APIRouter(prefix="/internal", tags=["internal"])


class EchoRequest(BaseModel):
    message: str


@router.post("/echo", dependencies=[Depends(require_service_signature)])
async def echo(payload: EchoRequest) -> dict:
    return {
        "service": "risk-service",
        "echo": payload.message,
        "traceId": get_trace_id(),
        "receivedAt": datetime.now(UTC).isoformat(),
    }
