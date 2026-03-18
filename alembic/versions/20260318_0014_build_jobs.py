"""add build jobs

Revision ID: 20260318_0014
Revises: 20260317_0013
Create Date: 2026-03-18 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_0014"
down_revision = "20260317_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "build_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("current_stage", sa.String(length=64), nullable=False, server_default="accepted"),
        sa.Column("executor_name", sa.String(length=128), nullable=True),
        sa.Column("failure_class", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_build_jobs_attempt", "build_jobs", ["attempt"], unique=False)
    op.create_index("ix_build_jobs_build_id", "build_jobs", ["build_id"], unique=False)
    op.create_index("ix_build_jobs_current_stage", "build_jobs", ["current_stage"], unique=False)
    op.create_index("ix_build_jobs_started_at", "build_jobs", ["started_at"], unique=False)
    op.create_index("ix_build_jobs_status", "build_jobs", ["status"], unique=False)
    op.create_index("ix_build_jobs_updated_at", "build_jobs", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_build_jobs_updated_at", table_name="build_jobs")
    op.drop_index("ix_build_jobs_status", table_name="build_jobs")
    op.drop_index("ix_build_jobs_started_at", table_name="build_jobs")
    op.drop_index("ix_build_jobs_current_stage", table_name="build_jobs")
    op.drop_index("ix_build_jobs_build_id", table_name="build_jobs")
    op.drop_index("ix_build_jobs_attempt", table_name="build_jobs")
    op.drop_table("build_jobs")
