"""SQLAlchemy models for the return-risk context (risk_db)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapter.output.persistence.base import Base


class ReturnRiskAssessmentModel(Base):
    __tablename__ = "return_risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True)
    score: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(16))
    decision: Mapped[str] = mapped_column(String(16))
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    factors: Mapped[list[ReturnRiskFactorModel]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan", lazy="selectin"
    )


class ReturnRiskFactorModel(Base):
    __tablename__ = "return_risk_factors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("return_risk_assessments.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(256))
    weight: Mapped[int] = mapped_column(Integer)
    contribution: Mapped[int] = mapped_column(Integer)

    assessment: Mapped[ReturnRiskAssessmentModel] = relationship(back_populates="factors")
