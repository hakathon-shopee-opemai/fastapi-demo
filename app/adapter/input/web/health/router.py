"""Liveness/readiness probe checking DB + Redis."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config.database.engine import check_db
from app.config.redis.client import check_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    db_ok = await check_db()
    redis_ok = await check_redis()
    up = db_ok and redis_ok
    body = {
        "status": "UP" if up else "DOWN",
        "components": {
            "db": "UP" if db_ok else "DOWN",
            "redis": "UP" if redis_ok else "DOWN",
        },
    }
    return JSONResponse(status_code=200 if up else 503, content=body)
