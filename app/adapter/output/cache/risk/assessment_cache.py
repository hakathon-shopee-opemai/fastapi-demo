"""Redis cache of assessments keyed by order id (idempotent reads)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from redis.asyncio import Redis

from app.domain.risk.aggregate.assessment import RiskAssessment
from app.domain.risk.entity.factor import RiskFactor
from app.domain.risk.vo.types import RiskDecision, RiskFactorCode, RiskLevel


def _serialize(a: RiskAssessment) -> dict:
    return {
        "id": str(a.id),
        "order_id": a.order_id,
        "customer_id": a.customer_id,
        "score": a.score,
        "level": str(a.level),
        "decision": str(a.decision),
        "fingerprint": a.fingerprint,
        "assessed_at": a.assessed_at.isoformat(),
        "factors": [
            {"code": str(f.code), "description": f.description, "weight": f.weight, "contribution": f.contribution}
            for f in a.factors
        ],
    }


def _deserialize(d: dict) -> RiskAssessment:
    return RiskAssessment(
        id=uuid.UUID(d["id"]),
        order_id=d["order_id"],
        customer_id=d["customer_id"],
        score=d["score"],
        level=RiskLevel(d["level"]),
        decision=RiskDecision(d["decision"]),
        factors=tuple(
            RiskFactor(RiskFactorCode(f["code"]), f["description"], f["weight"], f["contribution"])
            for f in d["factors"]
        ),
        assessed_at=datetime.fromisoformat(d["assessed_at"]),
        fingerprint=d["fingerprint"],
    )


class RedisAssessmentCache:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def _key(order_id: str) -> str:
        return f"risk:assessment:{order_id}"

    async def get(self, order_id: str) -> RiskAssessment | None:
        raw = await self._redis.get(self._key(order_id))
        return _deserialize(json.loads(raw)) if raw else None

    async def put(self, assessment: RiskAssessment, ttl_seconds: int) -> None:
        await self._redis.set(self._key(assessment.order_id), json.dumps(_serialize(assessment)), ex=ttl_seconds)
