"""SQLAlchemy implementation of ReturnRiskRepositoryPort (upsert by order_id)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapter.output.persistence.return_risk.entity.models import ReturnRiskAssessmentModel
from app.adapter.output.persistence.return_risk.mapper.mapper import to_domain, to_model
from app.domain.return_risk.aggregate.assessment import ReturnRiskAssessment


class SqlAlchemyReturnRiskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, assessment: ReturnRiskAssessment) -> ReturnRiskAssessment:
        existing = await self._session.scalar(
            select(ReturnRiskAssessmentModel).where(
                ReturnRiskAssessmentModel.order_id == assessment.order_id
            )
        )
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()
        self._session.add(to_model(assessment))
        await self._session.commit()
        return assessment

    async def find_by_order_id(self, order_id: str) -> ReturnRiskAssessment | None:
        model = await self._session.scalar(
            select(ReturnRiskAssessmentModel).where(ReturnRiskAssessmentModel.order_id == order_id)
        )
        return to_domain(model) if model is not None else None
