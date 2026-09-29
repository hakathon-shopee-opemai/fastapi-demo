"""Map between web schemas and application/domain types for the return-risk context."""
from __future__ import annotations

from app.adapter.input.web.return_risk.schema.request.schemas import ReturnAssessmentRequest
from app.adapter.input.web.return_risk.schema.response.schemas import (
    ReturnAssessmentResponse,
    ReturnFactorResponse,
)
from app.application.return_risk.dto.commands import AssessReturnRiskCommand
from app.domain.return_risk.aggregate.assessment import ReturnRiskAssessment


def to_command(req: ReturnAssessmentRequest) -> AssessReturnRiskCommand:
    return AssessReturnRiskCommand(
        order_id=req.orderId,
        customer_id=req.customerId,
        order_total=req.orderTotal,
        requested_amount=req.requestedAmount,
        currency=req.currency,
        reason=req.reasonCode,
        tier=req.customerTier,
        days_since_order=req.daysSinceOrder,
    )


def to_response(a: ReturnRiskAssessment) -> ReturnAssessmentResponse:
    return ReturnAssessmentResponse(
        assessmentId=str(a.id),
        orderId=a.order_id,
        score=a.score,
        level=str(a.level),
        decision=str(a.decision),
        factors=[
            ReturnFactorResponse(
                code=str(f.code),
                description=f.description,
                weight=f.weight,
                contribution=f.contribution,
            )
            for f in a.factors
        ],
        assessedAt=a.assessed_at.isoformat(),
    )
