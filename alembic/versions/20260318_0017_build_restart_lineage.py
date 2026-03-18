"""add build restart lineage

Revision ID: 20260318_0017
Revises: 20260318_0016
Create Date: 2026-03-18 05:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_0017"
down_revision = "20260318_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("build_attempts", sa.Column("restarted_from_attempt", sa.Integer(), nullable=True))
    op.add_column("build_attempts", sa.Column("restarted_from_job_id", sa.String(length=64), nullable=True))
    op.add_column("build_attempts", sa.Column("restart_reason", sa.String(length=255), nullable=True))
    op.create_index(
        op.f("ix_build_attempts_restarted_from_job_id"),
        "build_attempts",
        ["restarted_from_job_id"],
        unique=False,
    )

    op.add_column("build_jobs", sa.Column("restarted_from_attempt", sa.Integer(), nullable=True))
    op.add_column("build_jobs", sa.Column("restarted_from_job_id", sa.String(length=64), nullable=True))
    op.add_column("build_jobs", sa.Column("restart_reason", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_build_jobs_restarted_from_job_id"), "build_jobs", ["restarted_from_job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_build_jobs_restarted_from_job_id"), table_name="build_jobs")
    op.drop_column("build_jobs", "restart_reason")
    op.drop_column("build_jobs", "restarted_from_job_id")
    op.drop_column("build_jobs", "restarted_from_attempt")

    op.drop_index(op.f("ix_build_attempts_restarted_from_job_id"), table_name="build_attempts")
    op.drop_column("build_attempts", "restart_reason")
    op.drop_column("build_attempts", "restarted_from_job_id")
    op.drop_column("build_attempts", "restarted_from_attempt")
