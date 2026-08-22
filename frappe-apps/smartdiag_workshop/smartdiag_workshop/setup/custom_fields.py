from __future__ import annotations

import frappe

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS = {
    "Service Order": [
        {"fieldname": "sd_vehicle_section", "fieldtype": "Section Break", "label": "SmartDiag Vehicle"},
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "customer"},
        {"fieldname": "sd_vehicle", "fieldtype": "Link", "label": "Vehicle", "options": "SmartDiag Vehicle", "reqd": 1, "insert_after": "sd_external_reference"},
        {"fieldname": "sd_check_in", "fieldtype": "Link", "label": "Check In", "options": "Vehicle Check In", "insert_after": "sd_vehicle"},
        {"fieldname": "sd_odometer", "fieldtype": "Int", "label": "Odometer", "insert_after": "sd_check_in"},
        {"fieldname": "sd_promised_at", "fieldtype": "Datetime", "label": "Promised At", "insert_after": "due_date"},
        {"fieldname": "sd_workshop_bay", "fieldtype": "Link", "label": "Workshop Bay", "options": "Workshop Bay", "insert_after": "sd_promised_at"},
        {"fieldname": "sd_workflow_state", "fieldtype": "Select", "label": "SmartDiag State", "options": "CREATED\nQUOTED_BY_TECHNICIAN\nPENDING_CUSTOMER_APPROVAL\nPENDING_PARTS\nREADY_TO_INVOICE\nINVOICED", "default": "CREATED", "insert_after": "status"},
        {"fieldname": "sd_transition_reason", "fieldtype": "Small Text", "label": "Transition Reason", "insert_after": "sd_workflow_state"},
        {"fieldname": "sd_invoice_reference", "fieldtype": "Link", "label": "Sales Invoice", "options": "Sales Invoice", "read_only": 1, "insert_after": "sd_transition_reason"},
        {"fieldname": "sd_quality_check", "fieldtype": "Link", "label": "Quality Check", "options": "Workshop Quality Check", "read_only": 1, "insert_after": "sd_workflow_state"},
        {"fieldname": "sd_platform_diagnosis", "fieldtype": "Long Text", "label": "Diagnóstico SmartDiag", "insert_after": "sd_transition_reason"},
        {"fieldname": "sd_platform_assigned_technicians", "fieldtype": "Small Text", "label": "Técnicos asignados SmartDiag", "insert_after": "sd_platform_diagnosis"},
        {"fieldname": "sd_platform_bay_code", "fieldtype": "Data", "label": "Bahía SmartDiag", "insert_after": "sd_platform_assigned_technicians"},
        {"fieldname": "sd_platform_parts_json", "fieldtype": "JSON", "label": "Repuestos SmartDiag", "read_only": 1, "insert_after": "sd_platform_bay_code"},
        {"fieldname": "sd_platform_labor_json", "fieldtype": "JSON", "label": "Mano de obra SmartDiag", "read_only": 1, "insert_after": "sd_platform_parts_json"},
        {"fieldname": "sd_platform_evidence_json", "fieldtype": "JSON", "label": "Evidencia SmartDiag", "read_only": 1, "insert_after": "sd_platform_labor_json"},
        {"fieldname": "sd_platform_updated_at", "fieldtype": "Datetime", "label": "Actualizado por SmartDiag", "read_only": 1, "insert_after": "sd_platform_evidence_json"},
    ],
    "Service Quotation": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "party_name"},
        {"fieldname": "sd_vehicle", "fieldtype": "Link", "label": "Vehicle", "options": "SmartDiag Vehicle", "insert_after": "sd_external_reference"},
        {"fieldname": "sd_version", "fieldtype": "Int", "label": "Quotation Version", "default": 1, "read_only": 1, "insert_after": "sd_vehicle"},
        {"fieldname": "sd_approval_status", "fieldtype": "Select", "label": "Approval Status", "options": "DRAFT\nSENT\nPARTIALLY_APPROVED\nAPPROVED\nREJECTED\nEXPIRED", "default": "DRAFT", "insert_after": "status"},
        {"fieldname": "sd_approval_token_hash", "fieldtype": "Data", "label": "Approval Token Hash", "hidden": 1, "insert_after": "sd_approval_status"},
    ],
    "Stock Entry": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "stock_entry_type"},
    ],
    "Service Appointment": [
        {"fieldname": "sd_vehicle", "fieldtype": "Link", "label": "Vehicle", "options": "SmartDiag Vehicle", "insert_after": "customer"},
        {"fieldname": "sd_workshop_bay", "fieldtype": "Link", "label": "Workshop Bay", "options": "Workshop Bay", "insert_after": "sd_vehicle"},
    ],
    "Item": [
        {"fieldname": "sd_online_section", "fieldtype": "Section Break", "label": "SmartDiag Online Store", "insert_after": "is_sales_item"},
        {"fieldname": "sd_online_sellable", "fieldtype": "Check", "label": "Sellable Online", "default": 0, "insert_after": "sd_online_section"},
        {"fieldname": "sd_store_slug", "fieldtype": "Data", "label": "Store Slug", "unique": 1, "insert_after": "sd_online_sellable"},
        {"fieldname": "sd_oem_number", "fieldtype": "Data", "label": "OEM Number", "insert_after": "sd_store_slug"},
        {"fieldname": "sd_fitment_status", "fieldtype": "Select", "label": "Fitment Status", "options": "CONFIRMED\nPROBABLE\nREQUIRES_VALIDATION", "default": "REQUIRES_VALIDATION", "insert_after": "sd_oem_number"},
        {"fieldname": "sd_fitment_notes", "fieldtype": "Small Text", "label": "Fitment Notes", "insert_after": "sd_fitment_status"},
    ],
    "Customer": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "customer_name"},
        {"fieldname": "sd_whatsapp", "fieldtype": "Data", "label": "WhatsApp", "insert_after": "mobile_no"},
    ],
    "Employee": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "employee_name"},
        {"fieldname": "sd_technician_skills", "fieldtype": "Small Text", "label": "Technician Skills", "insert_after": "designation"},
        {"fieldname": "sd_primary_bay", "fieldtype": "Link", "label": "Primary Bay", "options": "Workshop Bay", "insert_after": "sd_technician_skills"},
    ],
    "Supplier": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "supplier_name"},
    ],
    "Purchase Order": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "supplier"},
    ],
    "Purchase Receipt": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "supplier"},
    ],
    "Landed Cost Voucher": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "company"},
    ],
    "Payroll Entry": [
        {"fieldname": "sd_external_reference", "fieldtype": "Data", "label": "SmartDiag External Reference", "unique": 1, "read_only": 1, "insert_after": "company"},
    ],
}


def install_custom_fields() -> None:
    # Existing fields are immutable deployment history. Rewriting them on every
    # migrate triggers Frappe Version formatting for legacy numeric defaults and
    # can abort an otherwise idempotent schema upgrade. New fields are still
    # created; intentional changes require an explicit patch migration.
    available_custom_fields = {
        doctype: fields
        for doctype, fields in CUSTOM_FIELDS.items()
        if frappe.db.exists("DocType", doctype)
    }
    create_custom_fields(available_custom_fields, update=False)
