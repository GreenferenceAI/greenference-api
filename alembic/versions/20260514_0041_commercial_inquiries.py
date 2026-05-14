"""commercial_inquiries — inbound leads from the public /contact-sales form

Revision ID: 20260514_0041
Revises: 20260424_0040
Create Date: 2026-05-14
"""
from alembic import op
import sqlalchemy as sa


revision = "20260514_0041"
down_revision = "20260424_0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commercial_inquiries",
        sa.Column("inquiry_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), server_default=""),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), server_default=""),
        sa.Column("gpu_count", sa.Integer(), nullable=True),
        sa.Column("duration", sa.String(128), server_default=""),
        sa.Column("budget", sa.String(128), server_default=""),
        sa.Column("use_case", sa.Text(), nullable=True),
        sa.Column("source_ip", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("status", sa.String(32), server_default="new"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_commercial_inquiries_email", "commercial_inquiries", ["email"])
    op.create_index("ix_commercial_inquiries_status", "commercial_inquiries", ["status"])
    op.create_index("ix_commercial_inquiries_submitted_at", "commercial_inquiries", ["submitted_at"])


def downgrade() -> None:
    op.drop_index("ix_commercial_inquiries_submitted_at", table_name="commercial_inquiries")
    op.drop_index("ix_commercial_inquiries_status", table_name="commercial_inquiries")
    op.drop_index("ix_commercial_inquiries_email", table_name="commercial_inquiries")
    op.drop_table("commercial_inquiries")
