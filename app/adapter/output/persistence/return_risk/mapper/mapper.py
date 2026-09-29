"""Map between the ReturnRiskAssessment domain aggregate and ORM models."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.adapter.output.persistence.return_risk.entity.models import (
    ReturnRiskAssessmentModel,
    ReturnRiskFactorModel,
)
from app.domain.return_risk.aggregate.assessment import ReturnRiskAssessment
from app.domain.return_risk.entity.factor import ReturnRiskFactor
from app.domain.return_risk.vo.types import ReturnDecision, ReturnFactorCode, ReturnLevel


def to_model(a: ReturnRiskAssessment) -> ReturnRiskAssessmentModel:
    return ReturnRiskAssessmentModel(
        id=a.id,
        order_id=a.order_id,
        customer_id=a.customer_id,
        score=a.score,
        level=str(a.level),
        decision=str(a.decision),
        assessed_at=a.assessed_at,
        created_at=datetime.now(UTC),
        factors=[
            ReturnRiskFactorModel(
                id=uuid.uuid4(),
                code=str(f.code),
                description=f.description,
                weight=f.weight,
                contribution=f.contribution,
            )
            for f in a.factors
        ],
    )


def to_domain(m: ReturnRiskAssessmentModel) -> ReturnRiskAssessment:
    return ReturnRiskAssessment(
        id=m.id,
        order_id=m.order_id,
        customer_id=m.customer_id,
        score=m.score,
        level=ReturnLevel(m.level),
        decision=ReturnDecision(m.decision),
        factors=tuple(
            ReturnRiskFactor(ReturnFactorCode(f.code), f.description, f.weight, f.contribution)
            for f in m.factors
        ),
        assessed_at=m.assessed_at,
    )
