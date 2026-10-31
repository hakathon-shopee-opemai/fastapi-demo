"""FastAPI application factory for the risk-service (infrastructure wiring + business routers)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

# Import ORM models so their tables are registered on Base.metadata before create_all.
import app.adapter.output.persistence.return_risk.entity.models  # noqa: E402,F401
import app.adapter.output.persistence.risk.entity.models  # noqa: E402,F401
from app.adapter.input.web.auth.router import router as auth_router
from app.adapter.input.web.demo.router import router as demo_router
from app.adapter.input.web.health.router import router as health_router
from app.adapter.input.web.internal.saga_router import router as internal_saga_router
from app.adapter.input.web.return_risk.router.router import internal_return_risk_router
from app.adapter.input.web.risk.router.router import internal_risk_router, public_risk_router
from app.adapter.output.client.order.client import close_order_client, init_order_client
from app.adapter.output.persistence.base import Base
from app.common.exception.handler import register_exception_handlers
from app.common.logging.middleware import CorrelationIdMiddleware
from app.config.database.engine import dispose_engine, get_engine, init_engine
from app.config.logging.setup import configure_logging
from app.config.redis.client import close_redis, init_redis
from app.config.settings.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_engine(settings.database_url)
    init_redis(settings.redis_url)
    init_order_client()
    # Demo convenience: ensure tables exist (Alembic owns schema in real deployments).
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await close_order_client()
        await close_redis()
        await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.app_env)

    app = FastAPI(title="risk-service", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(internal_saga_router)
    app.include_router(internal_risk_router)
    app.include_router(internal_return_risk_router)
    app.include_router(auth_router)
    app.include_router(demo_router)
    app.include_router(public_risk_router)
    return app


app = create_app()
