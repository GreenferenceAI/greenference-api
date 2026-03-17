"""add miner auth secret

Revision ID: 20260317_0006
Revises: 20260317_0005
Create Date: 2026-03-17 00:06:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260317_0006"
down_revision = "20260317_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("miners", sa.Column("auth_secret", sa.String(length=255), nullable=True))
    op.execute("UPDATE miners SET auth_secret = hotkey || '-secret' WHERE auth_secret IS NULL")
    op.alter_column("miners", "auth_secret", nullable=False)


def downgrade() -> None:
    op.drop_column("miners", "auth_secret")
