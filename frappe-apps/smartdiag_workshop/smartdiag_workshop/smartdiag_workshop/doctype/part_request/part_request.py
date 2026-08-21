from __future__ import annotations

from frappe.model.document import Document
from frappe.utils import now_datetime

from smartdiag_workshop.events.outbox import enqueue_event


class PartRequest(Document):
    def before_insert(self):
        self.requested_at = self.requested_at or now_datetime()

    def on_submit(self):
        self.status = "PENDING"
        enqueue_event(
            event_type="PART_REQUEST_CREATED",
            aggregate_type=self.doctype,
            aggregate_id=self.name,
            payload={"service_order": self.service_order, "warehouse": self.warehouse},
        )
