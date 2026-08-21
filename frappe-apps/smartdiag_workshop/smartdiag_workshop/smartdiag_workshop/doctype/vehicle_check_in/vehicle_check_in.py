from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from smartdiag_workshop.events.outbox import enqueue_event


class VehicleCheckIn(Document):
    def before_insert(self):
        self.check_in_at = self.check_in_at or now_datetime()

    def validate(self):
        if self.vehicle:
            owner = frappe.db.get_value("SmartDiag Vehicle", self.vehicle, "customer")
            if owner and self.customer != owner:
                frappe.throw("Check-in customer must match the vehicle owner")

    def on_submit(self):
        enqueue_event(
            event_type="VEHICLE_CHECKED_IN",
            aggregate_type=self.doctype,
            aggregate_id=self.name,
            payload={"vehicle": self.vehicle, "odometer": self.odometer, "promised_at": self.promised_at},
        )
