"""Register exception handlers producing RFC-7807 problem+json responses."""
from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.exception.code import ErrorCode
from app.common.exception.model import PROBLEM_JSON, AppError, ProblemDetail
from app.common.logging.context import get_trace_id

_log = structlog.get_logger("app.error")

_STATUS_TO_CODE = {
    401: ErrorCode.UNAUTHENTICATED,
    403: ErrorCode.ACCESS_DENIED,
    404: ErrorCode.NOT_FOUND,
    429: ErrorCode.RATE_LIMITED,
}


def _problem_response(
    status: int, title: str, code: ErrorCode, detail: str | None, headers: dict | None = None
) -> JSONResponse:
    body = ProblemDetail(
        title=title, status=status, code=code, detail=detail, traceId=get_trace_id()
    ).model_dump(by_alias=True)
    return JSONResponse(
        status_code=status, content=body, media_type=PROBLEM_JSON, headers=headers
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return _problem_response(exc.status, exc.title, exc.code, exc.detail, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _problem_response(
            422, "Validation Error", ErrorCode.VALIDATION_ERROR, str(exc.errors())
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_TO_CODE.get(exc.status_code, ErrorCode.INTERNAL)
        title = code.value.replace("_", " ").title()
        headers = getattr(exc, "headers", None)
        return _problem_response(exc.status_code, title, code, str(exc.detail), headers)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        _log.exception("unhandled.exception", error=str(exc))
        return _problem_response(
            500, "Internal Server Error", ErrorCode.INTERNAL, "Unexpected error"
        )
