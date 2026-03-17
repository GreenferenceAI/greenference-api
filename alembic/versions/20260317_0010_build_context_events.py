"""add build context and event history

Revision ID: 20260317_0010
Revises: 20260317_0009
Create Date: 2026-03-17 00:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260317_0010"
down_revision = "20260317_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("builds", sa.Column("build_log_uri", sa.String(length=1024), nullable=True))
    op.add_column("builds", sa.Column("build_duration_seconds", sa.Float(), nullable=True))

    op.create_table(
        "build_contexts",
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("source_uri", sa.String(length=1024), nullable=False),
        sa.Column("normalized_context_uri", sa.String(length=1024), nullable=False),
        sa.Column("dockerfile_path", sa.String(length=256), nullable=False),
        sa.Column("dockerfile_object_uri", sa.String(length=1024), nullable=True),
        sa.Column("context_digest", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("build_id"),
    )

    op.create_table(
        "build_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_build_events_build_id", "build_events", ["build_id"])
    op.create_index("ix_build_events_stage", "build_events", ["stage"])
    op.create_index("ix_build_events_created_at", "build_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_build_events_created_at", table_name="build_events")
    op.drop_index("ix_build_events_stage", table_name="build_events")
    op.drop_index("ix_build_events_build_id", table_name="build_events")
    op.drop_table("build_events")
    op.drop_table("build_contexts")
    op.drop_column("builds", "build_duration_seconds")
    op.drop_column("builds", "build_log_uri")
