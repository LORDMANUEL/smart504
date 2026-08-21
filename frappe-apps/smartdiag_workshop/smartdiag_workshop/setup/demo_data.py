from __future__ import annotations

import frappe
from frappe.utils import now_datetime


def seed_workshop_demo() -> dict[str, str]:
    """Crea registros operativos mínimos únicamente cuando el sitio demo está vacío."""
    created: dict[str, str] = {}

    if not frappe.db.exists("Workshop Bay", {"bay_code": "BAHIA-01"}):
        bay = frappe.get_doc(
            {
                "doctype": "Workshop Bay",
                "bay_code": "BAHIA-01",
                "bay_name": "Diagnóstico y servicio rápido",
                "status": "FREE",
                "active": 1,
                "capabilities": "Diagnóstico, mantenimiento preventivo y frenos",
            }
        ).insert(ignore_permissions=True)
        created["workshop_bay"] = bay.name

    vehicle = frappe.get_all(
        "SmartDiag Vehicle",
        fields=["name", "customer", "odometer"],
        order_by="modified desc",
        limit=1,
    )
    service_order = frappe.get_all("Service Order", pluck="name", order_by="modified desc", limit=1)
    employee = frappe.get_all("Employee", pluck="name", filters={"status": "Active"}, limit=1)
    if vehicle:
        vehicle_row = vehicle[0]
        if not frappe.db.exists("Vehicle Check In", {"vehicle": vehicle_row.name}):
            check_in = frappe.get_doc(
                {
                    "doctype": "Vehicle Check In",
                    "vehicle": vehicle_row.name,
                    "customer": vehicle_row.customer,
                    "service_order": service_order[0] if service_order else None,
                    "check_in_at": now_datetime(),
                    "odometer": vehicle_row.odometer or 1,
                    "fuel_level": 50,
                    "reason": "Recepción demo para diagnóstico general",
                    "reported_symptoms": "Cliente solicita revisión preventiva y confirmación del diagnóstico.",
                    "status": "DRAFT",
                }
            ).insert(ignore_permissions=True)
            created["vehicle_check_in"] = check_in.name

        if service_order and employee and not frappe.db.exists(
            "Workshop Quality Check", {"service_order": service_order[0]}
        ):
            quality_check = frappe.get_doc(
                {
                    "doctype": "Workshop Quality Check",
                    "service_order": service_order[0],
                    "vehicle": vehicle_row.name,
                    "inspector": employee[0],
                    "inspection_at": now_datetime(),
                    "result": "PENDING",
                    "road_test_required": 1,
                    "road_test_result": "NOT_REQUIRED",
                    "notes": "Control demo pendiente de revisión final y evidencia fotográfica.",
                }
            ).insert(ignore_permissions=True)
            created["quality_check"] = quality_check.name

    frappe.db.commit()
    return created
