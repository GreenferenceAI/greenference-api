"""add build and invocation history

Revision ID: 20260317_0007
Revises: 20260317_0006
Create Date: 2026-03-17 00:07:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260317_0007"
down_revision = "20260317_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("builds", sa.Column("registry_repository", sa.String(length=512), nullable=True))
    op.add_column("builds", sa.Column("image_tag", sa.String(length=128), nullable=True))
    op.add_column("builds", sa.Column("artifact_digest", sa.String(length=128), nullable=True))
    op.add_column("builds", sa.Column("failure_reason", sa.Text(), nullable=True))

    op.create_table(
        "invocation_records",
        sa.Column("invocation_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("deployment_id", sa.String(length=64), nullable=False),
        sa.Column("workload_id", sa.String(length=64), nullable=False),
        sa.Column("hotkey", sa.String(length=128), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("api_key_id", sa.String(length=64), nullable=True),
        sa.Column("stream", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_class", sa.String(length=128), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("invocation_id"),
    )
    op.create_index("ix_invocation_records_request_id", "invocation_records", ["request_id"], unique=True)
    op.create_index("ix_invocation_records_deployment_id", "invocation_records", ["deployment_id"])
    op.create_index("ix_invocation_records_workload_id", "invocation_records", ["workload_id"])
    op.create_index("ix_invocation_records_hotkey", "invocation_records", ["hotkey"])
    op.create_index("ix_invocation_records_model", "invocation_records", ["model"])
    op.create_index("ix_invocation_records_api_key_id", "invocation_records", ["api_key_id"])
    op.create_index("ix_invocation_records_status", "invocation_records", ["status"])


def downgrade() -> None:
    op.drop_index("ix_invocation_records_status", table_name="invocation_records")
    op.drop_index("ix_invocation_records_api_key_id", table_name="invocation_records")
    op.drop_index("ix_invocation_records_model", table_name="invocation_records")
    op.drop_index("ix_invocation_records_hotkey", table_name="invocation_records")
    op.drop_index("ix_invocation_records_workload_id", table_name="invocation_records")
    op.drop_index("ix_invocation_records_deployment_id", table_name="invocation_records")
    op.drop_index("ix_invocation_records_request_id", table_name="invocation_records")
    op.drop_table("invocation_records")

    op.drop_column("builds", "failure_reason")
    op.drop_column("builds", "artifact_digest")
    op.drop_column("builds", "image_tag")
    op.drop_column("builds", "registry_repository")
