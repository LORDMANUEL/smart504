from __future__ import annotations

import json

from sqlalchemy import select

from app.db import SessionLocal
from app.models import WorkOrder
from app.request_context import set_staff_identity
from app.services.erp_outbox import enqueue_erp_job


def main() -> None:
    """Queue every legacy OT that still lacks authoritative ERP evidence."""
    queued = 0
    skipped = 0
    with SessionLocal() as db:
        work_orders = list(
            db.scalars(
                select(WorkOrder).execution_options(include_all_tenants=True)
            )
        )
        for work_order in work_orders:
            if work_order.erpnext_service_order_id:
                skipped += 1
                continue
            set_staff_identity(
                actor="erp-backfill",
                organization_id=work_order.organization_id,
                branch_id=None,
                is_recovery=True,
            )
            enqueue_erp_job(
                db,
                aggregate_type="WORK_ORDER",
                aggregate_id=work_order.id,
                operation="UPSERT_SERVICE_ORDER",
                idempotency_key=f"work-order:{work_order.id}:initial",
                payload={},
            )
            queued += 1
        db.commit()
    print(json.dumps({"queued": queued, "skipped": skipped}, sort_keys=True))


if __name__ == "__main__":
    main()
