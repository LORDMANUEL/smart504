"""Backfill reception and work-order steps into flow analytics.

Revision ID: 0006_flow_history_backfill
Revises: 0005_flow_events
"""

import sqlalchemy as sa

from alembic import op

revision: str = "0006_flow_history_backfill"
down_revision: str | None = "0005_flow_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(
        sa.text("""
        INSERT INTO flow_events
            (id, module, action, item_reference, actor, result, metadata_json, created_at)
        SELECT
            md5('booking:' || b.id), 'RECEPTION', 'BOOKING_CREATED', b.id,
            'migration-backfill', 'SUCCESS',
            jsonb_build_object('vehicle', b.vehicle_summary, 'service', b.service_requested,
                               'preferred_date', b.preferred_date),
            b.created_at
        FROM bookings b
        WHERE NOT EXISTS (
            SELECT 1 FROM flow_events f
            WHERE f.module = 'RECEPTION' AND f.action = 'BOOKING_CREATED'
              AND f.item_reference = b.id
        )
    """)
    )
    op.execute(
        sa.text("""
        INSERT INTO flow_events
            (id, module, action, item_reference, actor, result, metadata_json, created_at)
        SELECT
            md5('wo-event:' || e.id), 'WORK_ORDER',
            CASE WHEN e.event_type = 'WORK_ORDER_CREATED'
                 THEN 'WORK_ORDER_CREATED' ELSE 'STATUS_CHANGED' END,
            w.number, e.actor, 'SUCCESS',
            jsonb_build_object('event_type', e.event_type, 'from_status', e.from_status,
                               'to_status', e.to_status),
            e.created_at
        FROM work_order_events e
        JOIN work_orders w ON w.id = e.work_order_id
        WHERE e.event_type IN ('WORK_ORDER_CREATED', 'WORK_ORDER_STATUS_CHANGED')
          AND NOT EXISTS (
            SELECT 1 FROM flow_events f
            WHERE f.module = 'WORK_ORDER'
              AND f.item_reference = w.number
              AND f.created_at = e.created_at
          )
    """)
    )


def downgrade() -> None:
    # Historical analytics are append-only; rollback must not erase business events.
    pass
