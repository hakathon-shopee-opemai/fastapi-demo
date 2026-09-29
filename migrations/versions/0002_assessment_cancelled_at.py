"""add cancelled_at to risk_assessments

Revision ID: 0002_assessment_cancelled_at
Revises: 0001_init
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_assessment_cancelled_at"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "risk_assessments",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("risk_assessments", "cancelled_at")
