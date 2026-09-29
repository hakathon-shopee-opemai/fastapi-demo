"""SQLAlchemy implementation of RiskAssessmentRepositoryPort (upsert by order_id)."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapter.output.persistence.risk.entity.models import RiskAssessmentModel
from app.adapter.output.persistence.risk.mapper.mapper import to_domain, to_model
from app.domain.risk.aggregate.assessment import RiskAssessment


class SqlAlchemyRiskAssessmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, assessment: RiskAssessment) -> RiskAssessment:
        existing = await self._session.scalar(
            select(RiskAssessmentModel).where(RiskAssessmentModel.order_id == assessment.order_id)
        )
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()
        self._session.add(to_model(assessment))
        await self._session.commit()
        return assessment

    async def find_by_order_id(self, order_id: str) -> RiskAssessment | None:
        model = await self._session.scalar(
            select(RiskAssessmentModel).where(RiskAssessmentModel.order_id == order_id)
        )
        return to_domain(model) if model is not None else None

    async def mark_cancelled(self, order_id: str) -> str:
        """Stamp cancelled_at on the assessment for order_id. Idempotent no-op if absent.

        Returns "CANCELLED" if a row was matched (or already cancelled), else "NO_ASSESSMENT".
        """
        result = await self._session.execute(
            update(RiskAssessmentModel)
            .where(RiskAssessmentModel.order_id == order_id)
            .values(cancelled_at=datetime.now(UTC))
        )
        await self._session.commit()
        return "CANCELLED" if (result.rowcount or 0) > 0 else "NO_ASSESSMENT"
