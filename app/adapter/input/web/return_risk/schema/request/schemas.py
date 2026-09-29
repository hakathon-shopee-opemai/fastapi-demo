"""Inbound request schemas for the return-assessment endpoint."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.return_risk.vo.types import CustomerTier, ReturnReason


class ReturnAssessmentRequest(BaseModel):
    orderId: str
    customerId: str
    orderTotal: Decimal = Field(ge=0)
    requestedAmount: Decimal = Field(ge=0)
    currency: str = "USD"
    reasonCode: ReturnReason
    customerTier: CustomerTier = CustomerTier.STANDARD
    daysSinceOrder: int = Field(ge=0)
