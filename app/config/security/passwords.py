"""Constant-time demo credential check (no user store in the demo)."""
from __future__ import annotations

import hmac

from app.config.settings.settings import get_settings


def verify_credentials(username: str, password: str) -> bool:
    settings = get_settings()
    user_ok = hmac.compare_digest(username or "", settings.auth_demo_username)
    pass_ok = hmac.compare_digest(password or "", settings.auth_demo_password)
    return user_ok and pass_ok
