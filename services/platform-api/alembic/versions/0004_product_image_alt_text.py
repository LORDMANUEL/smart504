"""Persist accessible alternative text for catalog product images.

Revision ID: 0004_product_image_alt_text
Revises: 0003_store_orders
Create Date: 2026-08-12
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_product_image_alt_text"
down_revision: str | None = "0003_store_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A temporary server default safely backfills installations that already
    # contain images. New records are always required to provide meaningful
    # alt text through the application API.
    op.add_column(
        "catalog_product_images",
        sa.Column(
            "alt_text",
            sa.String(length=240),
            nullable=False,
            server_default="Imagen de repuesto",
        ),
    )
    op.alter_column(
        "catalog_product_images",
        "alt_text",
        existing_type=sa.String(length=240),
        nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("catalog_product_images", "alt_text")
