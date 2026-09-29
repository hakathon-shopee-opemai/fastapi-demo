"""Correlation-id propagation via contextvars, shared by stdlib logging + structlog."""
from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

_trace_id: ContextVar[str] = ContextVar("trace_id", default="-")
_span_id: ContextVar[str] = ContextVar("span_id", default="-")

TRACE_HEADER = "X-Trace-Id"


def get_trace_id() -> str:
    return _trace_id.get()


def set_trace_id(value: str | None) -> str:
    tid = value or new_trace_id()
    _trace_id.set(tid)
    return tid


def get_span_id() -> str:
    return _span_id.get()


def set_span_id(value: str | None) -> str:
    sid = value or new_span_id()
    _span_id.set(sid)
    return sid


def new_trace_id() -> str:
    return uuid.uuid4().hex


def new_span_id() -> str:
    return uuid.uuid4().hex[:16]


class CorrelationIdFilter(logging.Filter):
    """Inject trace_id/span_id onto every LogRecord so formatters can render them."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        record.span_id = get_span_id()
        return True


def add_correlation_ids(logger, method_name, event_dict):  # structlog processor
    event_dict.setdefault("trace_id", get_trace_id())
    event_dict.setdefault("span_id", get_span_id())
    return event_dict
