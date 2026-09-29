"""Map between the RiskAssessment domain aggregate and ORM models."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.adapter.output.persistence.risk.entity.models import RiskAssessmentModel, RiskFactorModel
from app.domain.risk.aggregate.assessment import RiskAssessment
from app.domain.risk.entity.factor import RiskFactor
from app.domain.risk.vo.types import RiskDecision, RiskFactorCode, RiskLevel


def to_model(a: RiskAssessment) -> RiskAssessmentModel:
    return RiskAssessmentModel(
        id=a.id,
        order_id=a.order_id,
        customer_id=a.customer_id,
        score=a.score,
        level=str(a.level),
        decision=str(a.decision),
        fingerprint=a.fingerprint,
        assessed_at=a.assessed_at,
        created_at=datetime.now(UTC),
        factors=[
            RiskFactorModel(
                id=uuid.uuid4(),
                code=str(f.code),
                description=f.description,
                weight=f.weight,
                contribution=f.contribution,
            )
            for f in a.factors
        ],
    )


def to_domain(m: RiskAssessmentModel) -> RiskAssessment:
    return RiskAssessment(
        id=m.id,
        order_id=m.order_id,
        customer_id=m.customer_id,
        score=m.score,
        level=RiskLevel(m.level),
        decision=RiskDecision(m.decision),
        factors=tuple(
            RiskFactor(RiskFactorCode(f.code), f.description, f.weight, f.contribution) for f in m.factors
        ),
        assessed_at=m.assessed_at,
        fingerprint=m.fingerprint,
    )
