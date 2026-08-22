from __future__ import annotations

import frappe
from frappe.utils import flt


@frappe.whitelist(allow_guest=True)
def list_products(q: str | None = None, start: int = 0, page_length: int = 24):
    filters = {"disabled": 0, "is_sales_item": 1, "sd_online_sellable": 1}
    or_filters = None
    if q:
        like = f"%{q.strip()}%"
        or_filters = {"item_code": ["like", like], "item_name": ["like", like], "description": ["like", like]}
    items = frappe.get_all(
        "Item",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "item_code",
            "item_name",
            "description",
            "image",
            "sd_store_slug",
            "sd_oem_number",
            "sd_fitment_status",
            "sd_fitment_notes",
        ],
        start=int(start),
        page_length=min(int(page_length), 100),
        order_by="item_name asc",
    )
    return {"items": items, "total": len(items)}


def _upsert_item(entry: dict, *, is_service: bool) -> None:
    code = entry["code"]
    values = {
        "item_name": entry["description"],
        "description": entry["description"],
        "item_group": "Workshop Services" if is_service else "Workshop Parts",
        "stock_uom": "Hour" if is_service else entry.get("unit") or "Nos",
        "is_stock_item": 0 if is_service else 1,
        "is_sales_item": 1,
        "is_purchase_item": 0 if is_service else 1,
        "disabled": 0 if entry.get("active", True) else 1,
        "valuation_rate": flt(entry["cost_price"]),
    }
    if frappe.db.exists("Item", code):
        item = frappe.get_doc("Item", code)
        item.update(values)
        item.save(ignore_permissions=True)
    else:
        frappe.get_doc({"doctype": "Item", "item_code": code, **values}).insert(
            ignore_permissions=True
        )

    price_name = frappe.db.get_value(
        "Item Price", {"item_code": code, "price_list": "Standard Selling", "currency": "HNL"}, "name"
    )
    price_values = {"price_list_rate": flt(entry["sale_price"]), "selling": 1, "currency": "HNL"}
    if price_name:
        price = frappe.get_doc("Item Price", price_name)
        price.update(price_values)
        price.save(ignore_permissions=True)
    else:
        frappe.get_doc(
            {"doctype": "Item Price", "item_code": code, "price_list": "Standard Selling", **price_values}
        ).insert(ignore_permissions=True)

    if is_service:
        labor_values = {
            "title": entry["description"],
            "item_code": code,
            "standard_hours": flt(entry["standard_hours"]),
            "default_rate": flt(entry["sale_price"]),
            "active": 1 if entry.get("active", True) else 0,
        }
        if frappe.db.exists("Labor Operation", code):
            labor = frappe.get_doc("Labor Operation", code)
            labor.update(labor_values)
            labor.save(ignore_permissions=True)
        else:
            frappe.get_doc(
                {"doctype": "Labor Operation", "operation_code": code, **labor_values}
            ).insert(ignore_permissions=True)


def _replace_fitments(entry: dict, catalog_type: str) -> None:
    frappe.db.delete("Vehicle Fitment", {"catalog_type": catalog_type, "catalog_code": entry["code"]})
    for fitment in entry.get("fitments") or []:
        frappe.get_doc(
            {
                "doctype": "Vehicle Fitment",
                "catalog_type": catalog_type,
                "catalog_code": entry["code"],
                "vehicle_make": fitment["make"],
                "vehicle_model": fitment["model"],
                "year_from": fitment["year_from"],
                "year_to": fitment["year_to"],
                "engine": fitment.get("engine"),
                "active": 1 if entry.get("active", True) else 0,
            }
        ).insert(ignore_permissions=True)


@frappe.whitelist()
def import_workshop_catalog(catalog):
    """Apply a validated workbook payload to ERPNext in one transaction."""
    allowed_roles = {"System Manager", "SmartDiag Integration API"}
    if not allowed_roles.intersection(frappe.get_roles()):
        frappe.throw("Not permitted", frappe.PermissionError)
    payload = frappe.parse_json(catalog) if isinstance(catalog, str) else catalog
    errors = payload.get("errors") or []
    if errors:
        frappe.throw("Catalog import contains validation errors")
    for entry in payload.get("labor") or []:
        _upsert_item(entry, is_service=True)
        _replace_fitments(entry, "LABOR")
    for entry in payload.get("parts") or []:
        _upsert_item(entry, is_service=False)
        _replace_fitments(entry, "PART")
    return {"labor": len(payload.get("labor") or []), "parts": len(payload.get("parts") or [])}


@frappe.whitelist()
def compatible_catalog(vehicle_make: str, vehicle_model: str, vehicle_year: int, engine: str | None = None):
    filters = {
        "vehicle_make": vehicle_make,
        "vehicle_model": vehicle_model,
        "year_from": ["<=", int(vehicle_year)],
        "year_to": [">=", int(vehicle_year)],
        "active": 1,
    }
    rows = frappe.get_all(
        "Vehicle Fitment",
        filters=filters,
        fields=["catalog_type", "catalog_code", "engine"],
        order_by="catalog_type, catalog_code",
    )
    normalized_engine = (engine or "").strip().casefold()
    return [
        row
        for row in rows
        if not row.engine or not normalized_engine or row.engine.strip().casefold() == normalized_engine
    ]
