from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from smartdiag_workshop.events.outbox import enqueue_event


class WorkshopQualityCheck(Document):
    def before_insert(self):
        self.inspection_at = self.inspection_at or now_datetime()

    def validate(self):
        failed = any(row.result == "FAIL" for row in self.checklist or [])
        if failed:
            self.result = "FAILED"
        if self.result == "PASSED" and self.road_test_required and self.road_test_result != "PASSED":
            frappe.throw("Road test must pass before quality control can pass")
        self.customer_ready = 1 if self.result == "PASSED" else 0

    def on_submit(self):
        enqueue_event(
            event_type="QUALITY_CHECK_PASSED" if self.result == "PASSED" else "QUALITY_CHECK_FAILED",
            aggregate_type=self.doctype,
            aggregate_id=self.service_order,
            payload={"quality_check": self.name, "result": self.result},
        )
