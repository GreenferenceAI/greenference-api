"""inference demand stats

Per-minute bucketed invocation counts keyed by (model_id, window_start).
Validator worker consumes `inference.invoked` bus events and increments
the current-minute row for each model. Feeds Flux's demand-reactive
replica-target calculation.

48-hour retention is enforced by the validator worker loop (DELETE rows
older than 48h) — no TTL machinery in Postgres.

Revision ID: 20260422_0039
Revises: 20260422_0038
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa


revision = "20260422_0039"
down_revision = "20260422_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inference_demand_stats",
        sa.Column("model_id", sa.String(128), primary_key=True),
        sa.Column("window_start", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("invocations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt_tokens_sum", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("completion_tokens_sum", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("latency_ms_sum", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_inference_demand_stats_window",
        "inference_demand_stats",
        ["window_start"],
    )


def downgrade() -> None:
    op.drop_index("ix_inference_demand_stats_window", table_name="inference_demand_stats")
    op.drop_table("inference_demand_stats")
