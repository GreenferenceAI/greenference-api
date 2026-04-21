"""deployments.metering_remainder_mcents — fractional-cent accumulator

The per-minute metering loop charges integer cents, but most rate/count
combinations produce fractional cents per minute (1× 4090 = 0.67¢/min,
3× 5090 = 3.5¢/min, etc.). Plain `round()` over-charges 1× rentals by 50%
and under-charges 2× rentals by 25%.

Fix: carry a fractional remainder (in millicents) on each deployment row.
Each cycle we add the minute's cost in millicents, then debit
`remainder // 1000` whole cents and keep the sub-cent remainder for next
tick. Over an hour the total converges exactly to the hourly rate.

Revision ID: 20260421_0036
Revises: 20260421_0035
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa


revision = "20260421_0036"
down_revision = "20260421_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployments",
        sa.Column(
            "metering_remainder_mcents",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("deployments", "metering_remainder_mcents")
