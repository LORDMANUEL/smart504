"""Add authenticated appointments, quotes and cashier accounting.

Revision ID: 0007_client_calendar_cashier
Revises: 0006_flow_history_backfill
"""

import sqlalchemy as sa

from alembic import op

revision: str = "0007_client_calendar_cashier"
down_revision: str | None = "0006_flow_history_backfill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("customer_id", sa.String(36), nullable=True))
    op.add_column("bookings", sa.Column("vehicle_id", sa.String(80), nullable=True))
    op.add_column("bookings", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("duration_minutes", sa.Integer(), nullable=True))
    op.create_index("ix_bookings_customer_id", "bookings", ["customer_id"])
    op.create_index("ix_bookings_vehicle_id", "bookings", ["vehicle_id"])
    op.create_index("ix_bookings_scheduled_at", "bookings", ["scheduled_at"])

    op.create_table(
        "quotes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("number", sa.String(40), nullable=False, unique=True),
        sa.Column(
            "work_order_id",
            sa.String(36),
            sa.ForeignKey("work_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("discount", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_by", sa.String(120), nullable=False),
        sa.Column("approved_by", sa.String(120)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quotes_number", "quotes", ["number"])
    op.create_index("ix_quotes_work_order_id", "quotes", ["work_order_id"])
    op.create_index("ix_quotes_status", "quotes", ["status"])
    op.create_table(
        "quote_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "quote_id",
            sa.String(36),
            sa.ForeignKey("quotes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("line_type", sa.String(30), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quote_lines_quote_id", "quote_lines", ["quote_id"])
    op.create_table(
        "cash_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("opened_by", sa.String(120), nullable=False),
        sa.Column("closed_by", sa.String(120)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("opening_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("counted_cash", sa.Numeric(12, 2)),
        sa.Column("expected_cash", sa.Numeric(12, 2)),
        sa.Column("difference", sa.Numeric(12, 2)),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cash_sessions_status", "cash_sessions", ["status"])
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("receipt_number", sa.String(40), nullable=False, unique=True),
        sa.Column(
            "cash_session_id",
            sa.String(36),
            sa.ForeignKey("cash_sessions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "work_order_id",
            sa.String(36),
            sa.ForeignKey("work_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quote_id", sa.String(36), sa.ForeignKey("quotes.id", ondelete="SET NULL")),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reference", sa.String(180)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("received_by", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payments_receipt_number", "payments", ["receipt_number"])
    op.create_index("ix_payments_cash_session_id", "payments", ["cash_session_id"])
    op.create_index("ix_payments_work_order_id", "payments", ["work_order_id"])
    op.create_index("ix_payments_quote_id", "payments", ["quote_id"])
    op.create_index("ix_payments_method", "payments", ["method"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("cash_sessions")
    op.drop_table("quote_lines")
    op.drop_table("quotes")
    op.drop_index("ix_bookings_scheduled_at", table_name="bookings")
    op.drop_index("ix_bookings_vehicle_id", table_name="bookings")
    op.drop_index("ix_bookings_customer_id", table_name="bookings")
    op.drop_column("bookings", "duration_minutes")
    op.drop_column("bookings", "scheduled_at")
    op.drop_column("bookings", "vehicle_id")
    op.drop_column("bookings", "customer_id")
