"""Logging bootstrap: load dictConfig YAML + wire structlog to the stdlib backend."""
from __future__ import annotations

import logging
import logging.config
from pathlib import Path

import structlog
import yaml

from app.common.logging.context import CorrelationIdFilter, add_correlation_ids

_CONFIG_DIR = Path(__file__).resolve().parent


def _config_path(app_env: str) -> Path:
    if app_env == "docker":
        return _CONFIG_DIR / "logging.docker.yaml"
    return _CONFIG_DIR / "logging.yaml"


def configure_logging(app_env: str = "local") -> None:
    path = _config_path(app_env)
    with path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    # Replace the placeholder correlation filter with the real one.
    filters = config.setdefault("filters", {})
    filters["correlation"] = {"()": "app.common.logging.context.CorrelationIdFilter"}

    # Ensure the log directory exists for any RotatingFileHandler.
    for handler in config.get("handlers", {}).values():
        filename = handler.get("filename")
        if filename:
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(config)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_correlation_ids,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.stdlib.render_to_log_kwargs,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    # Silence unused-import complaints; the class must be importable for dictConfig.
    _ = CorrelationIdFilter
