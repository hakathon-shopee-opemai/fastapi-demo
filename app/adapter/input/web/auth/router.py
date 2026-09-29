"""Login endpoint issuing a JWT (demo credentials)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.common.exception.code import ErrorCode
from app.common.exception.model import AppError
from app.config.security.jwt import create_access_token
from app.config.security.passwords import verify_credentials

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int

    model_config = {"populate_by_name": True}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    if not verify_credentials(payload.username, payload.password):
        raise AppError(ErrorCode.UNAUTHENTICATED, 401, "Invalid username or password")
    token, ttl = create_access_token(payload.username)
    return TokenResponse(access_token=token, expires_in=ttl)
