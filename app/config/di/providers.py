"""Dependency wiring: build risk use cases from adapters (per-request)."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapter.output.cache.risk.assessment_cache import RedisAssessmentCache
from app.adapter.output.cache.risk.velocity import RedisVelocityCounter
from app.adapter.output.client.order.history_adapter import HttpCustomerHistoryAdapter
from app.adapter.output.persistence.risk.repository.sqlalchemy_repo import SqlAlchemyRiskAssessmentRepository
from app.application.risk.usecase.assess import AssessOrderRiskService
from app.application.risk.usecase.get import GetAssessmentService
from app.application.risk.usecase.saga import AdjustVelocityService, CancelAssessmentService
from app.config.redis.client import get_redis


def build_assess_usecase(session: AsyncSession) -> AssessOrderRiskService:
    redis = get_redis()
    return AssessOrderRiskService(
        repository=SqlAlchemyRiskAssessmentRepository(session),
        cache=RedisAssessmentCache(redis),
        velocity=RedisVelocityCounter(redis),
        history=HttpCustomerHistoryAdapter(),
    )


def build_get_usecase(session: AsyncSession) -> GetAssessmentService:
    return GetAssessmentService(SqlAlchemyRiskAssessmentRepository(session))


def build_velocity_adjust() -> AdjustVelocityService:
    return AdjustVelocityService(RedisVelocityCounter(get_redis()))


def build_cancel_assessment(session: AsyncSession) -> CancelAssessmentService:
    return CancelAssessmentService(SqlAlchemyRiskAssessmentRepository(session))
