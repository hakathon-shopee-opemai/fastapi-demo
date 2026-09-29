"""HMAC-SHA256 request signing/verification for internal service-to-service calls.

Canonical string (MUST match the Spring peer):
    METHOD + "\n" + PATH + "\n" + TS + "\n" + sha256hex(rawBody)
signature = lowercase hex of HMAC_SHA256(shared_secret, canonical)
"""
from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import Request

from app.common.exception.code import ErrorCode
from app.common.exception.model import AppError
from app.config.settings.settings import get_settings

SIGNATURE_HEADER = "X-Signature"
TIMESTAMP_HEADER = "X-Signature-Ts"


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def build_canonical(method: str, path: str, ts: str, body: bytes) -> str:
    return "\n".join([method.upper(), path, ts, sha256_hex(body)])


def sign(method: str, path: str, ts: str, body: bytes, secret: str | None = None) -> str:
    secret = secret or get_settings().service_shared_secret
    canonical = build_canonical(method, path, ts, body)
    return hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()


def verify(method: str, path: str, ts: str, body: bytes, signature: str) -> None:
    settings = get_settings()
    try:
        skew = abs(int(time.time()) - int(ts))
    except (TypeError, ValueError) as exc:
        raise AppError(ErrorCode.SIGNATURE_INVALID, 401, "Bad signature timestamp") from exc
    if skew > settings.signature_max_skew_seconds:
        raise AppError(ErrorCode.SIGNATURE_INVALID, 401, "Signature timestamp out of range")
    expected = sign(method, path, ts, body, settings.service_shared_secret)
    if not hmac.compare_digest(expected, signature or ""):
        raise AppError(ErrorCode.SIGNATURE_INVALID, 401, "Invalid service signature")


async def require_service_signature(request: Request) -> None:
    """FastAPI dependency: verify the HMAC signature of an internal request."""
    signature = request.headers.get(SIGNATURE_HEADER)
    ts = request.headers.get(TIMESTAMP_HEADER)
    if not signature or not ts:
        raise AppError(ErrorCode.UNAUTHENTICATED, 401, "Missing service signature headers")
    body = await request.body()
    verify(request.method, request.url.path, ts, body, signature)
