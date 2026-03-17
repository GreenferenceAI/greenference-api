"""add workload aliases and ingress hosts

Revision ID: 20260317_0009
Revises: 20260317_0008
Create Date: 2026-03-17 00:09:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260317_0009"
down_revision = "20260317_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workloads", sa.Column("workload_alias", sa.String(length=100), nullable=True))
    op.add_column("workloads", sa.Column("ingress_host", sa.String(length=255), nullable=True))
    op.create_index("ix_workloads_workload_alias", "workloads", ["workload_alias"], unique=True)
    op.create_index("ix_workloads_ingress_host", "workloads", ["ingress_host"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_workloads_ingress_host", table_name="workloads")
    op.drop_index("ix_workloads_workload_alias", table_name="workloads")
    op.drop_column("workloads", "ingress_host")
    op.drop_column("workloads", "workload_alias")
