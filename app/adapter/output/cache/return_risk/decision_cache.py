"""Redis cache of return decisions keyed by order id (idempotent reads)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from redis.asyncio import Redis

from app.domain.return_risk.aggregate.assessment import ReturnRiskAssessment
from app.domain.return_risk.entity.factor import ReturnRiskFactor
from app.domain.return_risk.vo.types import ReturnDecision, ReturnFactorCode, ReturnLevel


def _serialize(a: ReturnRiskAssessment) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "order_id": a.order_id,
        "customer_id": a.customer_id,
        "score": a.score,
        "level": str(a.level),
        "decision": str(a.decision),
        "assessed_at": a.assessed_at.isoformat(),
        "factors": [
            {
                "code": str(f.code),
                "description": f.description,
                "weight": f.weight,
                "contribution": f.contribution,
            }
            for f in a.factors
        ],
    }


def _deserialize(d: dict[str, Any]) -> ReturnRiskAssessment:
    return ReturnRiskAssessment(
        id=uuid.UUID(d["id"]),
        order_id=d["order_id"],
        customer_id=d["customer_id"],
        score=d["score"],
        level=ReturnLevel(d["level"]),
        decision=ReturnDecision(d["decision"]),
        factors=tuple(
            ReturnRiskFactor(
                ReturnFactorCode(f["code"]), f["description"], f["weight"], f["contribution"]
            )
            for f in d["factors"]
        ),
        assessed_at=datetime.fromisoformat(d["assessed_at"]),
    )


class RedisReturnDecisionCache:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def _key(order_id: str) -> str:
        return f"return:decision:{order_id}"

    async def get(self, order_id: str) -> ReturnRiskAssessment | None:
        raw = await self._redis.get(self._key(order_id))
        return _deserialize(json.loads(raw)) if raw else None

    async def put(self, assessment: ReturnRiskAssessment, ttl_seconds: int) -> None:
        await self._redis.set(
            self._key(assessment.order_id), json.dumps(_serialize(assessment)), ex=ttl_seconds
        )
