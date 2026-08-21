from __future__ import annotations

import frappe
from frappe.model.document import Document
from smartdiag_domain.vin import validate_vin


class SmartDiagVehicle(Document):
    def validate(self):
        try:
            self.vin = validate_vin(self.vin)
        except ValueError as exc:
            frappe.throw(str(exc))
        if self.plate:
            self.plate = "".join(self.plate.upper().split())
        if self.year and not 1900 <= int(self.year) <= 2100:
            frappe.throw("Vehicle year must be between 1900 and 2100")
