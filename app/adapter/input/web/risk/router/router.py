"""Risk-assessment routes: internal assess (HMAC) + public read (JWT)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapter.input.web.risk.mapper.mapper import to_command, to_response
from app.adapter.input.web.risk.schema.request.schemas import AssessRiskRequest
from app.adapter.input.web.risk.schema.response.schemas import AssessmentResponse
from app.common.exception.code import ErrorCode
from app.common.exception.model import AppError
from app.common.ratelimit import rate_limited
from app.config.database.engine import get_session
from app.config.di.providers import build_assess_usecase, build_get_usecase
from app.config.security.hmac import require_service_signature
from app.config.security.jwt import get_current_user

internal_risk_router = APIRouter(prefix="/internal", tags=["internal-risk"])
public_risk_router = APIRouter(prefix="/api/v1", tags=["risk"])


@internal_risk_router.post(
    "/risk-assessments",
    response_model=AssessmentResponse,
    dependencies=[Depends(require_service_signature)],
)
@rate_limited("risk.assess", permits=200, window_seconds=60)
async def assess_risk(request: AssessRiskRequest, session: AsyncSession = Depends(get_session)) -> AssessmentResponse:
    assessment = await build_assess_usecase(session).assess(to_command(request))
    return to_response(assessment)


@public_risk_router.get("/risk-assessments/{order_id}", response_model=AssessmentResponse)
async def get_assessment(
    order_id: str,
    _user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AssessmentResponse:
    assessment = await build_get_usecase(session).get(order_id)
    if assessment is None:
        raise AppError(ErrorCode.NOT_FOUND, 404, f"No assessment for order {order_id}")
    return to_response(assessment)
