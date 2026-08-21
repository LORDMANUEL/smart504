from __future__ import annotations

import frappe
from frappe.utils import add_days, today


def create_due_notifications() -> None:
    due = frappe.get_all(
        "Maintenance Recommendation",
        filters={"status": "OPEN", "due_date": ["<=", add_days(today(), 7)]},
        fields=["name", "vehicle", "due_date"],
    )
    for row in due:
        if not frappe.db.exists("ToDo", {"reference_type": "Maintenance Recommendation", "reference_name": row.name}):
            frappe.get_doc(
                {
                    "doctype": "ToDo",
                    "description": f"Maintenance due for {row.vehicle} on {row.due_date}",
                    "reference_type": "Maintenance Recommendation",
                    "reference_name": row.name,
                    "allocated_to": "Administrator",
                }
            ).insert(ignore_permissions=True)
