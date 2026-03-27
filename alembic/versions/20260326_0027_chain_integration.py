"""add bittensor chain integration tables

Revision ID: 20260326_0027
Revises: 20260326_0026
Create Date: 2026-03-26 00:27:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260326_0027"
down_revision = "20260326_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metagraph_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("netuid", sa.Integer(), nullable=False, index=True),
        sa.Column("uid", sa.Integer(), nullable=False, index=True),
        sa.Column("hotkey", sa.String(128), nullable=False, index=True),
        sa.Column("coldkey", sa.String(128), nullable=False),
        sa.Column("stake", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trust", sa.Float(), nullable=False, server_default="0"),
        sa.Column("incentive", sa.Float(), nullable=False, server_default="0"),
        sa.Column("emission", sa.Float(), nullable=False, server_default="0"),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "chain_weight_commits",
        sa.Column("commit_id", sa.String(64), primary_key=True),
        sa.Column("netuid", sa.Integer(), nullable=False, index=True),
        sa.Column("tx_hash", sa.String(128), nullable=False),
        sa.Column("uids", sa.JSON(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("chain_weight_commits")
    op.drop_table("metagraph_entries")
