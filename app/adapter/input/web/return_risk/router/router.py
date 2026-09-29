"""Return-assessment route: internal assess (HMAC-protected)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapter.input.web.return_risk.mapper.mapper import to_command, to_response
from app.adapter.input.web.return_risk.schema.request.schemas import ReturnAssessmentRequest
from app.adapter.input.web.return_risk.schema.response.schemas import ReturnAssessmentResponse
from app.config.database.engine import get_session
from app.config.di.providers import build_return_assess_usecase
from app.config.security.hmac import require_service_signature

internal_return_risk_router = APIRouter(prefix="/internal", tags=["internal-return-risk"])


@internal_return_risk_router.post(
    "/return-assessments",
    response_model=ReturnAssessmentResponse,
    dependencies=[Depends(require_service_signature)],
)
async def assess_return(
    request: ReturnAssessmentRequest, session: AsyncSession = Depends(get_session)
) -> ReturnAssessmentResponse:
    assessment = await build_return_assess_usecase(session).assess(to_command(request))
    return to_response(assessment)
