"""JWT issuing/verification (HS256) + FastAPI current-user dependency."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.common.exception.code import ErrorCode
from app.common.exception.model import AppError
from app.config.settings.settings import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

_ALG = "HS256"


def create_access_token(username: str) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(UTC)
    ttl = settings.auth_jwt_ttl_seconds
    claims = {
        "sub": username,
        "iss": settings.auth_jwt_issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    token = jwt.encode(claims, settings.auth_jwt_secret, algorithm=_ALG)
    return token, ttl


def decode_token(token: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    try:
        return jwt.decode(
            token,
            settings.auth_jwt_secret,
            algorithms=[_ALG],
            issuer=settings.auth_jwt_issuer,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AppError(ErrorCode.UNAUTHENTICATED, 401, "Invalid or expired token") from exc


async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> str:
    if not token:
        raise AppError(ErrorCode.UNAUTHENTICATED, 401, "Missing bearer token")
    claims = decode_token(token)
    return str(claims["sub"])
