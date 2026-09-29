"""Internal (HMAC) endpoints used by the order-service cancellation saga."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database.engine import get_session
from app.config.di.providers import build_cancel_assessment, build_velocity_adjust
from app.config.security.hmac import require_service_signature

router = APIRouter(prefix="/internal", tags=["internal-saga"])


class VelocityAdjustRequest(BaseModel):
    customerId: str
    delta: int = -1
    operationId: str


class VelocityAdjustResponse(BaseModel):
    customerId: str
    previousCount: int
    newCount: int
    applied: bool


class AssessmentCancelRequest(BaseModel):
    reason: str | None = None


class AssessmentCancelResponse(BaseModel):
    orderId: str
    status: str


@router.post(
    "/risk/velocity/adjust",
    response_model=VelocityAdjustResponse,
    dependencies=[Depends(require_service_signature)],
)
async def adjust_velocity(request: VelocityAdjustRequest) -> VelocityAdjustResponse:
    result = await build_velocity_adjust().adjust(
        request.customerId, request.delta, request.operationId
    )
    return VelocityAdjustResponse(
        customerId=request.customerId,
        previousCount=result.previous,
        newCount=result.new,
        applied=result.applied,
    )


@router.post(
    "/risk-assessments/{order_id}/cancel",
    response_model=AssessmentCancelResponse,
    dependencies=[Depends(require_service_signature)],
)
async def cancel_assessment(
    order_id: str,
    request: AssessmentCancelRequest,
    session: AsyncSession = Depends(get_session),
) -> AssessmentCancelResponse:
    status = await build_cancel_assessment(session).cancel(order_id)
    return AssessmentCancelResponse(orderId=order_id, status=status)
