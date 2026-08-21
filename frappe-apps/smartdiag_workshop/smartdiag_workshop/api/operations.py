from __future__ import annotations

import json
from datetime import UTC, date, datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import nowdate

from smartdiag_workshop.setup.integration import INTEGRATION_USER


def _require_integration_user() -> None:
    if frappe.session.user != INTEGRATION_USER:
        frappe.throw(_("SmartDiag integration credentials are required"), frappe.PermissionError)


def _mapping(value: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        frappe.throw(_("Command must be a JSON object"))
    return value


def _required(payload: dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        frappe.throw(_("Missing required integration field: {0}").format(key))
    return value


def _database_datetime(value: Any) -> str | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _ensure_customer(payload: dict[str, Any]) -> str:
    external_reference = str(_required(payload, "customer_id"))
    existing = frappe.db.get_value(
        "Customer", {"sd_external_reference": external_reference}, "name"
    )
    if existing:
        return str(existing)
    customer = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": str(_required(payload, "customer_name")),
            "customer_type": "Individual",
            "customer_group": "Individual",
            "territory": "All Territories",
            "mobile_no": payload.get("customer_phone"),
            "sd_whatsapp": payload.get("customer_phone"),
            "tax_id": payload.get("customer_tax_id"),
            "sd_external_reference": external_reference,
        }
    )
    customer.insert(ignore_permissions=True)
    return customer.name


def _ensure_vehicle(payload: dict[str, Any], customer: str) -> str:
    vin = str(_required(payload, "vin")).strip().upper()
    existing = frappe.db.get_value("SmartDiag Vehicle", {"vin": vin}, "name")
    values = {
        "customer": customer,
        "plate": payload.get("plate"),
        "make": str(_required(payload, "make")),
        "model": str(_required(payload, "model")),
        "year": int(_required(payload, "model_year")),
        "engine": payload.get("engine"),
        "odometer": payload.get("mileage_km"),
    }
    if existing:
        vehicle = frappe.get_doc("SmartDiag Vehicle", existing)
        vehicle.update(values)
        vehicle.save(ignore_permissions=True)
        return vehicle.name
    vehicle = frappe.get_doc({"doctype": "SmartDiag Vehicle", "vin": vin, **values})
    vehicle.insert(ignore_permissions=True)
    return vehicle.name


def _ensure_intake_item() -> str:
    """Provide Beveren's required, non-billable line until a quote is approved."""
    item_code = "SMARTDIAG-DIAGNOSTIC-INTAKE"
    if frappe.db.exists("Item", item_code):
        return item_code
    item_group = "Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups"
    frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Recepcion y diagnostico inicial",
            "description": "Linea operativa no facturable; se reemplaza con la cotizacion aprobada.",
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "is_sales_item": 1,
        }
    ).insert(ignore_permissions=True)
    return item_code


def _ensure_line_item(payload: dict[str, Any]) -> str:
    item_code = str(_required(payload, "item_code")).strip()
    if frappe.db.exists("Item", item_code):
        return item_code
    is_stock_item = bool(payload.get("is_stock_item"))
    item_group = "Products" if is_stock_item else "Services"
    if not frappe.db.exists("Item Group", item_group):
        item_group = "All Item Groups"
    frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": item_code,
            "item_name": payload.get("item_name") or item_code,
            "description": payload.get("description") or payload.get("item_name") or item_code,
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_stock_item": 1 if is_stock_item else 0,
            "is_sales_item": 1,
            "is_purchase_item": 1,
        }
    ).insert(ignore_permissions=True)
    return item_code


def _upsert_supplier(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "supplier_code"))
    existing = frappe.db.get_value("Supplier", {"sd_external_reference": external_reference}, "name")
    supplier_group = "SmartDiag Suppliers"
    if not frappe.db.exists("Supplier Group", supplier_group):
        frappe.get_doc({
            "doctype": "Supplier Group",
            "supplier_group_name": supplier_group,
            "parent_supplier_group": "All Supplier Groups",
            "is_group": 0,
        }).insert(ignore_permissions=True)
    values = {
        "supplier_name": str(_required(payload, "supplier_name")),
        "supplier_type": "Company",
        "supplier_group": supplier_group,
        "tax_id": payload.get("tax_id"),
        "sd_external_reference": external_reference,
    }
    if existing:
        document = frappe.get_doc("Supplier", existing); document.update(values); document.save(ignore_permissions=True)
    else:
        document = frappe.get_doc({"doctype": "Supplier", **values}); document.insert(ignore_permissions=True)
    return {"doctype": "Supplier", "name": document.name, "external_reference": external_reference}


def _supplier_for_purchase(payload: dict[str, Any]) -> str:
    reference = str(_required(payload, "supplier_code"))
    supplier = frappe.db.get_value("Supplier", {"sd_external_reference": reference}, "name")
    if supplier:
        return str(supplier)
    return str(_upsert_supplier(payload)["name"])


def _upsert_purchase_order(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "purchase_order_number"))
    company = str(_required(payload, "company"))
    supplier = _supplier_for_purchase(payload)
    existing = frappe.db.get_value("Purchase Order", {"sd_external_reference": external_reference}, "name")
    schedule_date = str(payload.get("expected_at") or date.today().isoformat())[:10]
    warehouse = _warehouse_name(str(payload.get("warehouse") or "BODEGA-STOCK"), company)
    items = []
    for row in payload.get("items") or []:
        item_code = _ensure_line_item({"item_code": row.get("sku"), "item_name": row.get("description"), "is_stock_item": True})
        items.append({"item_code": item_code, "item_name": row.get("description") or item_code,
                      "description": row.get("description") or item_code, "qty": row.get("quantity") or 0,
                      "rate": row.get("unit_cost") or 0, "schedule_date": schedule_date, "uom": "Nos", "stock_uom": "Nos",
                      "warehouse": warehouse})
    if not items:
        frappe.throw(_("A Purchase Order requires at least one item"))
    values = {"supplier": supplier, "company": company, "transaction_date": nowdate(),
              "schedule_date": schedule_date, "currency": payload.get("currency") or frappe.db.get_value("Company", company, "default_currency"),
              "conversion_rate": payload.get("exchange_rate") or 1, "sd_external_reference": external_reference, "items": items}
    if existing:
        document = frappe.get_doc("Purchase Order", existing)
        if document.docstatus == 0:
            document.update(values); document.save(ignore_permissions=True)
    else:
        document = frappe.get_doc({"doctype": "Purchase Order", **values}); document.insert(ignore_permissions=True)
    requested_status = str(payload.get("status") or "DRAFT")
    if requested_status in {"SUBMITTED", "APPROVED", "PARTIALLY_RECEIVED", "RECEIVED"} and document.docstatus == 0:
        document.submit()
    receipt_name = None
    requested_receipt_items = payload.get("items") if payload.get("receipt_reference") else None
    if requested_status == "RECEIVED" or requested_receipt_items:
        receipt_reference = str(payload.get("receipt_reference") or f"{external_reference}-RECEIPT")
        receipt_name = frappe.db.get_value("Purchase Receipt", {"sd_external_reference": receipt_reference}, "name")
        if not receipt_name:
            requested_by_code = {str(row.get("sku")): row.get("quantity") for row in (requested_receipt_items or [])}
            receipt_rows = []
            for row in document.items:
                quantity = requested_by_code.get(str(row.item_code), row.qty if not requested_receipt_items else 0)
                if quantity and float(quantity) > 0:
                    receipt_rows.append({"item_code": row.item_code, "item_name": row.item_name, "description": row.description,
                           "qty": quantity, "rate": row.rate, "uom": row.uom, "stock_uom": row.stock_uom,
                           "warehouse": warehouse, "purchase_order": document.name,
                           "purchase_order_item": row.name})
            if not receipt_rows:
                frappe.throw(_("The purchase receipt has no valid quantities"))
            # Use the PO transaction date as the minimum accounting date.  The
            # Frappe site timezone and the container UTC date can differ around
            # midnight; a receipt may never post before its source order.
            receipt_posting_date = str(document.transaction_date or date.today().isoformat())
            receipt = frappe.get_doc({"doctype": "Purchase Receipt", "supplier": supplier, "company": company,
                "posting_date": receipt_posting_date, "set_posting_time": 1,
                "currency": document.currency, "conversion_rate": document.conversion_rate,
                "sd_external_reference": receipt_reference,
                "items": receipt_rows})
            receipt.insert(ignore_permissions=True); receipt.submit(); receipt_name = receipt.name
    return {"doctype": "Purchase Order", "name": document.name, "external_reference": external_reference, "purchase_receipt": receipt_name}


def _submit_landed_cost(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "import_number"))
    existing = frappe.db.get_value("Landed Cost Voucher", {"sd_external_reference": external_reference}, "name")
    if existing:
        document = frappe.get_doc("Landed Cost Voucher", existing)
        if document.docstatus == 0: document.submit()
        return {"doctype": "Landed Cost Voucher", "name": document.name, "external_reference": external_reference}
    purchase_order = str(_required(payload, "purchase_order"))
    receipt = frappe.db.get_value("Purchase Receipt Item", {"purchase_order": purchase_order, "docstatus": 1}, "parent")
    if receipt and frappe.db.get_value("Purchase Receipt", receipt, "docstatus") != 1:
        receipt = None
    if not receipt:
        frappe.throw(_("The Purchase Receipt must be submitted before landed costs"))
    company = str(_required(payload, "company"))
    expense_account = frappe.db.get_value("Account", {"company": company, "root_type": "Expense", "is_group": 0}, "name")
    if not expense_account:
        frappe.throw(_("No expense account is configured for landed costs"))
    taxes = [{"description": row.get("description") or row.get("kind"), "amount": row.get("amount") or 0,
              "expense_account": expense_account} for row in payload.get("costs") or []]
    if not taxes: frappe.throw(_("At least one import cost is required"))
    receipt_posting_date = frappe.db.get_value("Purchase Receipt", receipt, "posting_date")
    document = frappe.get_doc({"doctype": "Landed Cost Voucher", "company": company,
        "posting_date": str(receipt_posting_date or nowdate()), "set_posting_time": 1,
        "sd_external_reference": external_reference, "distribute_charges_based_on": {"BY_VALUE": "Amount", "BY_QUANTITY": "Quantity", "BY_WEIGHT": "Distribute Manually"}.get(payload.get("allocation_method"), "Amount"),
        "purchase_receipts": [{"receipt_document_type": "Purchase Receipt", "receipt_document": receipt}], "taxes": taxes})
    document.insert(ignore_permissions=True); document.submit()
    return {"doctype": "Landed Cost Voucher", "name": document.name, "external_reference": external_reference}


def _upsert_employee(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "employee_code"))
    existing = frappe.db.get_value("Employee", {"sd_external_reference": external_reference}, "name")
    full_name = str(_required(payload, "employee_name")).strip(); parts = full_name.split(maxsplit=1)
    designation = str(payload.get("job_title") or "Tecnico")
    if not frappe.db.exists("Designation", designation):
        frappe.get_doc({"doctype": "Designation", "designation_name": designation}).insert(ignore_permissions=True)
    values = {"first_name": parts[0], "last_name": parts[1] if len(parts) > 1 else "SmartDiag",
              "company": str(_required(payload, "company")), "date_of_joining": str(_required(payload, "start_date")),
              "date_of_birth": str(_required(payload, "date_of_birth")),
              "status": "Active" if payload.get("status") == "ACTIVE" else "Inactive", "gender": "Prefer not to say",
              "designation": designation, "sd_external_reference": external_reference}
    optional_fields = {"personal_email": payload.get("email"), "cell_number": payload.get("phone"),
        "current_address": payload.get("address"), "health_insurance_no": payload.get("social_security_number")}
    employee_meta = frappe.get_meta("Employee")
    values.update({field: value for field, value in optional_fields.items() if value and employee_meta.has_field(field)})
    if not frappe.db.exists("Gender", "Prefer not to say"):
        values["gender"] = frappe.db.get_value("Gender", {}, "name")
    if existing:
        document = frappe.get_doc("Employee", existing); document.update(values); document.save(ignore_permissions=True)
    else:
        document = frappe.get_doc({"doctype": "Employee", **values}); document.insert(ignore_permissions=True)
    return {"doctype": "Employee", "name": document.name, "external_reference": external_reference}


def _submit_payroll(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "payroll_number"))
    if not frappe.db.exists("DocType", "Payroll Entry"):
        frappe.throw(_("HRMS Payroll Entry is not installed"))
    existing = frappe.db.get_value("Payroll Entry", {"sd_external_reference": external_reference}, "name")
    if existing:
        return {"doctype": "Payroll Entry", "name": existing, "external_reference": external_reference}
    company = str(_required(payload, "company"))
    currency = frappe.db.get_value("Company", company, "default_currency")
    payable_account = frappe.db.get_value("Company", company, "default_payroll_payable_account")
    if not payable_account:
        payable_account = frappe.db.get_value(
            "Account", {"company": company, "root_type": "Liability", "is_group": 0}, "name"
        )
    if not payable_account:
        frappe.throw(_("No payroll payable account is configured for the company"))
    employees = []
    for line in payload.get("lines") or []:
        employee = frappe.db.get_value("Employee", {"sd_external_reference": line.get("employee_code")}, "name")
        if not employee:
            frappe.throw(_("Employee {0} is not synchronized").format(line.get("employee_code")))
        employees.append({"employee": employee})
    document = frappe.get_doc({"doctype": "Payroll Entry", "company": company,
        "posting_date": str(_required(payload, "period_end")), "start_date": str(_required(payload, "period_start")),
        "end_date": str(_required(payload, "period_end")), "payroll_frequency": str(payload.get("payroll_frequency") or "Monthly"),
        "currency": currency, "exchange_rate": 1, "payroll_payable_account": payable_account,
        "sd_external_reference": external_reference, "employees": employees})
    document.insert(ignore_permissions=True)
    return {"doctype": "Payroll Entry", "name": document.name, "external_reference": external_reference, "docstatus": document.docstatus}


def _upsert_used_vehicle_item(payload: dict[str, Any]) -> dict[str, Any]:
    vin = str(_required(payload, "vin")).upper(); item_code = f"USED-{vin}"
    if frappe.db.exists("Item", item_code):
        document = frappe.get_doc("Item", item_code)
    else:
        document = frappe.get_doc({"doctype": "Item", "item_code": item_code,
            "item_name": f"{payload.get('make')} {payload.get('model')} {payload.get('model_year')}",
            "description": f"Vehiculo usado VIN {vin}", "item_group": "Products", "stock_uom": "Nos",
            "is_stock_item": 1, "has_serial_no": 1, "serial_no_series": f"{vin}.#", "is_sales_item": 1, "is_purchase_item": 1})
        document.insert(ignore_permissions=True)
    return {"doctype": "Item", "name": document.name, "external_reference": vin}


def _upsert_service_quotation(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "quote_number"))
    company = str(_required(payload, "company"))
    customer = _ensure_customer(payload)
    vehicle = _ensure_vehicle(payload, customer)
    existing = frappe.db.get_value(
        "Service Quotation", {"sd_external_reference": external_reference}, "name"
    )
    company_currency = frappe.db.get_value("Company", company, "default_currency")
    price_list = payload.get("selling_price_list") or "Standard Selling"
    price_currency = frappe.db.get_value("Price List", price_list, "currency") or company_currency
    items = []
    for row in payload.get("items") or []:
        item_code = _ensure_line_item(row)
        items.append(
            {
                "item_code": item_code,
                "item_name": row.get("item_name") or item_code,
                "description": row.get("description") or row.get("item_name") or item_code,
                "qty": row.get("qty") or 1,
                "uom": "Nos",
                "stock_uom": "Nos",
                "rate": row.get("rate") or 0,
                "price_list_rate": row.get("rate") or 0,
                "is_billable": 1,
            }
        )
    if not items:
        frappe.throw(_("A Service Quotation requires at least one approved or pending line"))
    values = {
        "quotation_to": "Customer",
        "party_name": customer,
        "company": company,
        "posting_date": date.today().isoformat(),
        "due_date": date.today().isoformat(),
        "priority": "Medium",
        "type": "Service",
        "selling_price_list": price_list,
        "price_list_currency": price_currency,
        "plc_conversion_rate": 1,
        "currency": price_currency,
        "conversion_rate": 1,
        "sd_external_reference": external_reference,
        "sd_vehicle": vehicle,
        "sd_approval_status": str(payload.get("status") or "DRAFT"),
        "preference_note": payload.get("notes"),
        "items": items,
    }
    if existing:
        document = frappe.get_doc("Service Quotation", existing)
        if document.docstatus != 0:
            if str(payload.get("status")) == "APPROVED":
                return {"doctype": "Service Quotation", "name": document.name, "external_reference": external_reference}
            frappe.throw(_("Submitted Service Quotation cannot be changed"))
        document.update(values)
        document.save(ignore_permissions=True)
    else:
        document = frappe.get_doc({"doctype": "Service Quotation", **values})
        document.insert(ignore_permissions=True)
    if str(payload.get("status")) == "APPROVED" and document.docstatus == 0:
        document.submit()
    return {
        "doctype": "Service Quotation",
        "name": document.name,
        "external_reference": external_reference,
        "approval_status": document.sd_approval_status,
    }


def _warehouse_name(code: str, company: str) -> str:
    existing = frappe.db.get_value(
        "Warehouse", {"warehouse_name": code, "company": company, "is_group": 0}, "name"
    )
    if existing:
        return str(existing)
    abbreviation = frappe.db.get_value("Company", company, "abbr")
    warehouse = frappe.get_doc(
        {
            "doctype": "Warehouse",
            "warehouse_name": code,
            "company": company,
            "parent_warehouse": f"All Warehouses - {abbreviation}",
            "is_group": 0,
        }
    )
    warehouse.insert(ignore_permissions=True)
    return warehouse.name


def _submit_stock_transfer(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "transfer_number"))
    existing = frappe.db.get_value(
        "Stock Entry", {"sd_external_reference": external_reference}, "name"
    )
    if existing:
        document = frappe.get_doc("Stock Entry", existing)
        if document.docstatus == 0:
            document.submit()
        return {"doctype": "Stock Entry", "name": document.name, "external_reference": external_reference}
    company = str(_required(payload, "company"))
    source = _warehouse_name(str(_required(payload, "from_warehouse")), company)
    target = _warehouse_name(str(_required(payload, "to_warehouse")), company)
    items = []
    for row in payload.get("items") or []:
        row = {**row, "is_stock_item": True}
        item_code = _ensure_line_item(row)
        items.append(
            {
                "item_code": item_code,
                "qty": row.get("qty") or 0,
                "transfer_qty": row.get("qty") or 0,
                "uom": "Nos",
                "stock_uom": "Nos",
                "s_warehouse": source,
                "t_warehouse": target,
            }
        )
    if not items:
        frappe.throw(_("A Stock Entry requires at least one item"))
    document = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Transfer",
            "purpose": "Material Transfer",
            "company": company,
            "sd_external_reference": external_reference,
            "items": items,
        }
    )
    document.insert(ignore_permissions=True)
    document.submit()
    return {"doctype": "Stock Entry", "name": document.name, "external_reference": external_reference}


def _upsert_service_order(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "work_order_number"))
    company = str(_required(payload, "company"))
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Configured ERPNext company does not exist: {0}").format(company))
    customer = _ensure_customer(payload)
    vehicle = _ensure_vehicle(payload, customer)
    existing = frappe.db.get_value(
        "Service Order", {"sd_external_reference": external_reference}, "name"
    )
    company_currency = frappe.db.get_value("Company", company, "default_currency")
    price_list = payload.get("selling_price_list") or "Standard Selling"
    price_currency = (
        frappe.db.get_value("Price List", price_list, "currency") or company_currency
    )
    values = {
        "title": str(_required(payload, "title")),
        "customer": customer,
        "company": company,
        "posting_date": payload.get("posting_date") or date.today().isoformat(),
        "due_date": payload.get("due_date") or date.today().isoformat(),
        "priority": payload.get("priority") or "Medium",
        "type": payload.get("service_type") or "Service",
        "status": "Open",
        "selling_price_list": price_list,
        "price_list_currency": price_currency,
        "plc_conversion_rate": 1,
        "currency": price_currency,
        "conversion_rate": 1,
        "sd_external_reference": external_reference,
        "sd_vehicle": vehicle,
        "sd_workflow_state": str(payload.get("status") or "CREATED"),
        "sd_promised_at": _database_datetime(payload.get("promised_at")),
        "preference_note": payload.get("concern"),
        "sd_platform_diagnosis": payload.get("diagnosis"),
        "sd_platform_assigned_technicians": "\n".join(payload.get("assigned_technicians") or []),
        "sd_platform_bay_code": payload.get("bay_code"),
        "sd_platform_parts_json": frappe.as_json(payload.get("parts_required") or []),
        "sd_platform_labor_json": frappe.as_json(payload.get("labor_entries") or []),
        "sd_platform_evidence_json": frappe.as_json(payload.get("evidence") or []),
        "sd_platform_updated_at": _database_datetime(payload.get("platform_updated_at")),
    }
    if existing:
        document = frappe.get_doc("Service Order", existing)
        if document.docstatus != 0:
            frappe.throw(_("Submitted Service Order cannot be changed by projection sync"))
        document.update(values)
        document.save(ignore_permissions=True)
    else:
        intake_item = _ensure_intake_item()
        document = frappe.get_doc(
            {
                "doctype": "Service Order",
                **values,
                "total_qty": 1,
                "base_total": 0,
                "base_net_total": 0,
                "total": 0,
                "net_total": 0,
                "base_total_taxes_and_charges": 0,
                "total_taxes_and_charges": 0,
                "base_grand_total": 0,
                "grand_total": 0,
                "items": [
                    {
                        "item_code": intake_item,
                        "item_name": "Recepcion y diagnostico inicial",
                        "description": "Pendiente de cotizacion y aprobacion del cliente.",
                        "qty": 1,
                        "uom": "Nos",
                        "stock_uom": "Nos",
                        "rate": 0,
                        "amount": 0,
                        "base_rate": 0,
                        "base_amount": 0,
                        "net_rate": 0,
                        "net_amount": 0,
                        "base_net_rate": 0,
                        "base_net_amount": 0,
                        "is_service": 1,
                        "is_billable": 0,
                    }
                ],
            }
        )
        document.insert(ignore_permissions=True)
    return {
        "doctype": "Service Order",
        "name": document.name,
        "external_reference": external_reference,
        "workflow_state": document.sd_workflow_state,
    }


def _transition_service_order(payload: dict[str, Any]) -> dict[str, Any]:
    external_reference = str(_required(payload, "work_order_number"))
    name = frappe.db.get_value(
        "Service Order", {"sd_external_reference": external_reference}, "name"
    )
    if not name:
        frappe.throw(_("Service Order projection does not exist"))
    document = frappe.get_doc("Service Order", name)
    document.sd_transition_reason = str(_required(payload, "reason"))
    document.sd_workflow_state = str(_required(payload, "to_status"))
    if payload.get("invoice_reference"):
        document.sd_invoice_reference = payload["invoice_reference"]
    document.save(ignore_permissions=True)
    return {
        "doctype": "Service Order",
        "name": document.name,
        "external_reference": external_reference,
        "workflow_state": document.sd_workflow_state,
    }


@frappe.whitelist()
def apply_integration_command(command: dict[str, Any] | str) -> dict[str, Any]:
    """Apply one idempotent platform command to the ERP source of truth."""
    _require_integration_user()
    command = _mapping(command)
    operation = str(_required(command, "operation"))
    payload = _mapping(_required(command, "payload"))
    if operation == "UPSERT_SERVICE_ORDER":
        result = _upsert_service_order(payload)
    elif operation == "TRANSITION_SERVICE_ORDER":
        result = _transition_service_order(payload)
    elif operation == "UPSERT_SERVICE_QUOTATION":
        result = _upsert_service_quotation(payload)
    elif operation == "SUBMIT_STOCK_TRANSFER":
        result = _submit_stock_transfer(payload)
    elif operation == "UPSERT_SUPPLIER":
        result = _upsert_supplier(payload)
    elif operation == "UPSERT_PURCHASE_ORDER":
        result = _upsert_purchase_order(payload)
    elif operation == "SUBMIT_LANDED_COST":
        result = _submit_landed_cost(payload)
    elif operation == "UPSERT_EMPLOYEE":
        result = _upsert_employee(payload)
    elif operation == "SUBMIT_PAYROLL":
        result = _submit_payroll(payload)
    elif operation == "UPSERT_USED_VEHICLE_ITEM":
        result = _upsert_used_vehicle_item(payload)
    else:
        frappe.throw(_("Unsupported SmartDiag integration operation"))
    frappe.db.commit()
    return result
