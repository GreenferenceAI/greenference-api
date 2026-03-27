"""add utilization scoring columns to scorecards

Revision ID: 20260326_0028
Revises: 20260326_0027
Create Date: 2026-03-26 00:28:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260326_0028"
down_revision = "20260326_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scorecards", sa.Column("utilization_score", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("scorecards", sa.Column("rental_revenue_bonus", sa.Float(), nullable=False, server_default="0.0"))
    op.alter_column("scorecards", "utilization_score", server_default=None)
    op.alter_column("scorecards", "rental_revenue_bonus", server_default=None)


def downgrade() -> None:
    op.drop_column("scorecards", "rental_revenue_bonus")
    op.drop_column("scorecards", "utilization_score")
