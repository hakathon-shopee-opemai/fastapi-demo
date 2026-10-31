"""return risk schema

Revision ID: 0003_return_risk_assessments
Revises: 0002_assessment_cancelled_at
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_return_risk_assessments"
down_revision = "0002_assessment_cancelled_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "return_risk_assessments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("order_id", sa.String(64), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_return_risk_assessments_customer_id", "return_risk_assessments", ["customer_id"]
    )
    op.create_table(
        "return_risk_factors",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("return_risk_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("description", sa.String(256), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("contribution", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_return_risk_factors_assessment_id", "return_risk_factors", ["assessment_id"]
    )


def downgrade() -> None:
    op.drop_table("return_risk_factors")
    op.drop_table("return_risk_assessments")
