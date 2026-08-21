"""Add durable multichannel notification outbox.

Revision ID: 0020_notification_outbox
Revises: 0019_staff_security
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_notification_outbox"
down_revision = "0019_staff_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(60), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient", sa.String(254), nullable=False),
        sa.Column("subject", sa.String(240)),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("template_key", sa.String(80), nullable=False),
        sa.Column("aggregate_type", sa.String(40), nullable=False),
        sa.Column("aggregate_id", sa.String(120), nullable=False),
        sa.Column("idempotency_key", sa.String(180), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_reference", sa.String(180)),
        sa.Column("last_error", sa.String(500)),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_notification_org_idempotency"),
    )
    for column in ("organization_id", "channel", "recipient", "status", "provider_reference", "sent_at"):
        op.create_index(f"ix_notification_deliveries_{column}", "notification_deliveries", [column])
    op.create_index("ix_notification_org_status_scheduled", "notification_deliveries", ["organization_id", "status", "scheduled_at"])
    op.create_index("ix_notification_aggregate", "notification_deliveries", ["aggregate_type", "aggregate_id"])


def downgrade() -> None:
    op.drop_table("notification_deliveries")
