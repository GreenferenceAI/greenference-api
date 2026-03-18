"""add build and workload product metadata

Revision ID: 20260318_0023
Revises: 20260318_0022
Create Date: 2026-03-18 03:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260318_0023"
down_revision = "20260318_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workloads", sa.Column("display_name", sa.String(length=128), nullable=True))
    op.add_column("workloads", sa.Column("readme", sa.Text(), nullable=True))
    op.add_column("workloads", sa.Column("logo_uri", sa.String(length=1024), nullable=True))
    op.add_column("workloads", sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.alter_column("workloads", "tags", server_default=None)

    op.add_column("builds", sa.Column("owner_user_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_builds_owner_user_id"), "builds", ["owner_user_id"], unique=False)
    op.add_column("builds", sa.Column("display_name", sa.String(length=128), nullable=True))
    op.add_column("builds", sa.Column("readme", sa.Text(), nullable=True))
    op.add_column("builds", sa.Column("logo_uri", sa.String(length=1024), nullable=True))
    op.add_column("builds", sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.alter_column("builds", "tags", server_default=None)


def downgrade() -> None:
    op.drop_column("builds", "tags")
    op.drop_column("builds", "logo_uri")
    op.drop_column("builds", "readme")
    op.drop_column("builds", "display_name")
    op.drop_index(op.f("ix_builds_owner_user_id"), table_name="builds")
    op.drop_column("builds", "owner_user_id")

    op.drop_column("workloads", "tags")
    op.drop_column("workloads", "logo_uri")
    op.drop_column("workloads", "readme")
    op.drop_column("workloads", "display_name")
