"""Allow a quote to exist before its work order.

Revision ID: 0009_prequotes_by_vehicle
Revises: 0008_operations_control_hub
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0009_prequotes_by_vehicle"
down_revision: str | None = "0008_operations_control_hub"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("quotes", "work_order_id", existing_type=sa.String(36), nullable=True)
    op.add_column("quotes", sa.Column("customer_id", sa.String(36)))
    op.add_column("quotes", sa.Column("vehicle_id", sa.String(36)))
    op.add_column("quotes", sa.Column("converted_work_order_id", sa.String(36)))
    op.create_index("ix_quotes_customer_id", "quotes", ["customer_id"])
    op.create_index("ix_quotes_vehicle_id", "quotes", ["vehicle_id"])
    op.create_foreign_key("fk_quotes_customer_id", "quotes", "customers", ["customer_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_quotes_vehicle_id", "quotes", "vehicles", ["vehicle_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_quotes_converted_work_order_id", "quotes", "work_orders", ["converted_work_order_id"], ["id"], ondelete="SET NULL")
    op.execute("UPDATE quotes SET customer_id = work_orders.customer_id, vehicle_id = work_orders.vehicle_id FROM work_orders WHERE quotes.work_order_id = work_orders.id")


def downgrade() -> None:
    op.drop_constraint("fk_quotes_converted_work_order_id", "quotes", type_="foreignkey")
    op.drop_constraint("fk_quotes_vehicle_id", "quotes", type_="foreignkey")
    op.drop_constraint("fk_quotes_customer_id", "quotes", type_="foreignkey")
    op.drop_index("ix_quotes_vehicle_id", table_name="quotes")
    op.drop_index("ix_quotes_customer_id", table_name="quotes")
    op.drop_column("quotes", "converted_work_order_id")
    op.drop_column("quotes", "vehicle_id")
    op.drop_column("quotes", "customer_id")
    op.alter_column("quotes", "work_order_id", existing_type=sa.String(36), nullable=False)
