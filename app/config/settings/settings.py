"""Application settings loaded from environment (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # runtime
    app_env: str = "local"
    service_name: str = "risk-service"

    # datastore
    database_url: str = "postgresql+asyncpg://parallax:parallax@localhost:5432/risk_db"
    redis_url: str = "redis://:parallax@localhost:6379/1"

    # peer (the reverse parallax hop)
    order_service_base_url: str = "http://localhost:8080"
    peer_connect_timeout_seconds: float = 2.0
    peer_read_timeout_seconds: float = 3.0

    # service-to-service HMAC
    service_shared_secret: str = "change-me-in-prod"
    signature_max_skew_seconds: int = 300

    # auth / JWT login
    auth_jwt_secret: str = "change-me-jwt-secret-min-32-bytes-long!!"
    auth_jwt_issuer: str = "parallax-risk-service"
    auth_jwt_ttl_seconds: int = 3600
    auth_demo_username: str = "demo"
    auth_demo_password: str = "demo1234"

    # rate limit (fixed window)
    rate_limit_capacity: int = 100
    rate_limit_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
