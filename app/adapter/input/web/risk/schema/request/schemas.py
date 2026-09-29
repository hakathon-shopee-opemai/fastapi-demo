"""Inbound request schemas for the risk-assessment endpoint."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class AssessLineRequest(BaseModel):
    productId: str
    quantity: int = Field(ge=1)
    unitPrice: Decimal = Field(ge=0)


class AssessRiskRequest(BaseModel):
    orderId: str
    customerId: str
    total: Decimal = Field(ge=0)
    currency: str = "USD"
    shippingCountry: str | None = None
    lines: list[AssessLineRequest] = Field(min_length=1)
