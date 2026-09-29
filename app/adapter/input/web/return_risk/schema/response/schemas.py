"""Outbound response schemas for the return-assessment endpoint."""
from __future__ import annotations

from pydantic import BaseModel


class ReturnFactorResponse(BaseModel):
    code: str
    description: str
    weight: int
    contribution: int


class ReturnAssessmentResponse(BaseModel):
    assessmentId: str
    orderId: str
    score: int
    level: str
    decision: str
    factors: list[ReturnFactorResponse]
    assessedAt: str
