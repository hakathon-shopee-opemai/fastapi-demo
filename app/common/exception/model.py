"""RFC-7807 problem detail model + application exception type."""
from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.common.exception.code import ErrorCode

PROBLEM_JSON = "application/problem+json"


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    code: ErrorCode
    trace_id: str = Field(alias="traceId")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    model_config = {"populate_by_name": True}


class AppError(Exception):
    """Raise from anywhere to produce a controlled problem+json response."""

    def __init__(
        self,
        code: ErrorCode,
        status: int,
        detail: str | None = None,
        title: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(detail or code.value)
        self.code = code
        self.status = status
        self.detail = detail
        self.title = title or code.value.replace("_", " ").title()
        self.headers = headers
