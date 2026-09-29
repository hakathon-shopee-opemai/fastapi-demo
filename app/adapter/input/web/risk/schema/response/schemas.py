"""Outbound response schemas for the risk-assessment endpoint."""
from __future__ import annotations

from pydantic import BaseModel


class FactorResponse(BaseModel):
    code: str
    description: str
    weight: int
    contribution: int


class AssessmentResponse(BaseModel):
    assessmentId: str
    orderId: str
    score: int
    level: str
    decision: str
    factors: list[FactorResponse]
    assessedAt: str
