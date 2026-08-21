"""Add persisted operational flow events.

Revision ID: 0005_flow_events
Revises: 0004_product_image_alt_text
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_flow_events"
down_revision: str | None = "0004_product_image_alt_text"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "flow_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("item_reference", sa.String(length=120), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_flow_events_created_at", "flow_events", ["created_at"])
    op.create_index("ix_flow_events_module_created", "flow_events", ["module", "created_at"])
    op.create_index("ix_flow_events_item_created", "flow_events", ["item_reference", "created_at"])


def downgrade() -> None:
    op.drop_table("flow_events")
