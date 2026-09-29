"""Map between web schemas and application/domain types."""
from __future__ import annotations

from app.adapter.input.web.risk.schema.request.schemas import AssessRiskRequest
from app.adapter.input.web.risk.schema.response.schemas import AssessmentResponse, FactorResponse
from app.application.risk.dto.commands import AssessOrderRiskCommand
from app.domain.risk.aggregate.assessment import RiskAssessment
from app.domain.risk.vo.snapshot import OrderLineSnapshot


def to_command(req: AssessRiskRequest) -> AssessOrderRiskCommand:
    return AssessOrderRiskCommand(
        order_id=req.orderId,
        customer_id=req.customerId,
        total=req.total,
        currency=req.currency,
        shipping_country=req.shippingCountry,
        lines=tuple(
            OrderLineSnapshot(product_id=ln.productId, quantity=ln.quantity, unit_price=ln.unitPrice)
            for ln in req.lines
        ),
    )


def to_response(a: RiskAssessment) -> AssessmentResponse:
    return AssessmentResponse(
        assessmentId=str(a.id),
        orderId=a.order_id,
        score=a.score,
        level=str(a.level),
        decision=str(a.decision),
        factors=[
            FactorResponse(code=str(f.code), description=f.description, weight=f.weight, contribution=f.contribution)
            for f in a.factors
        ],
        assessedAt=a.assessed_at.isoformat(),
    )
