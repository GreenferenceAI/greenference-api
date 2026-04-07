"""add ssh_private_key to deployments

Revision ID: 20260407_0030
Revises: 20260402_0029
Create Date: 2026-04-07 00:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260407_0030"
down_revision = "20260402_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deployments", sa.Column("ssh_private_key", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("deployments", "ssh_private_key")
