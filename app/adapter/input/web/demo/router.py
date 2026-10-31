"""JWT-protected demo endpoint (rate limited); the echo peer call was retired."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.common.ratelimit import rate_limit
from app.config.security.jwt import get_current_user

router = APIRouter(prefix="/api/v1/demo", tags=["demo"], dependencies=[Depends(rate_limit)])


@router.get("/whoami")
async def whoami(username: str = Depends(get_current_user)) -> dict:
    return {"username": username}
