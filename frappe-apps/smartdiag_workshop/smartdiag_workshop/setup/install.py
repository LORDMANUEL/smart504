from __future__ import annotations

import frappe

from .custom_fields import install_custom_fields

ROLES = [
    "Workshop Manager",
    "Service Advisor",
    "Workshop Technician",
    "Workshop Quality Inspector",
    "Parts Clerk",
    "Workshop Cashier",
]

DEMO_ADMIN_USERS = ("admin@smartdiag504.com", "demo.admin@smartdiag504.com")
DEMO_ADMIN_ROLES = (
    "Desk User",
    "System Manager",
    "Workshop Manager",
    "Service Advisor",
    "Stock Manager",
    "Sales Manager",
    "Purchase Manager",
    "Accounts Manager",
    "HR Manager",
)

ALLOWED_MODULES = {
    "Accounts",
    "Buying",
    "Selling",
    "Stock",
    "HR",
    "Payroll",
    "SmartDiag Workshop",
    "Field Service Management",
}

WORKSHOP_PERMISSIONS = {
    "Service Order": {
        "Workshop Manager": ("read", "select", "create", "write", "submit", "cancel", "print", "email", "report"),
        "Service Advisor": ("read", "select", "create", "write", "print", "email", "report"),
    },
    "Service Quotation": {
        "Workshop Manager": ("read", "select", "create", "write", "submit", "cancel", "print", "email", "report"),
        "Service Advisor": ("read", "select", "create", "write", "print", "email", "report"),
    },
    "SmartDiag Vehicle": {
        "Workshop Manager": ("read", "select", "create", "write", "print", "report"),
        "Service Advisor": ("read", "select", "create", "write", "print", "report"),
    },
    "Item": {
        "Workshop Manager": ("read", "select", "print", "report"),
        "Parts Clerk": ("read", "select", "print", "report"),
    },
}


def _set_single_values(doctype: str, values: dict[str, object]) -> None:
    """Configura sólo campos existentes para conservar compatibilidad entre versiones de Frappe."""
    meta = frappe.get_meta(doctype)
    for fieldname, value in values.items():
        if meta.has_field(fieldname):
            frappe.db.set_single_value(doctype, fieldname, value)


def configure_smartdiag_site() -> dict[str, object]:
    """Deja el escritorio ERP en español y con valores regionales seguros para Honduras."""
    _set_single_values(
        "System Settings",
        {
            "language": "es",
            "time_zone": "America/Tegucigalpa",
            "country": "Honduras",
            "date_format": "dd-mm-yyyy",
            "number_format": "#,###.##",
            "first_day_of_the_week": "Monday",
        },
    )
    _set_single_values("Global Defaults", {"default_currency": "HNL", "country": "Honduras"})
    _set_single_values(
        "Navbar Settings",
        {
            "app_logo": "/assets/smartdiag_workshop/smartdiag504-logo.png",
        },
    )
    user_meta = frappe.get_meta("User")
    administrator = frappe.get_doc("User", "Administrator")
    if user_meta.has_field("language"):
        administrator.language = "es"
    if user_meta.has_field("default_workspace"):
        administrator.default_workspace = "SmartDiag504"
    administrator.save(ignore_permissions=True)
    profile_name = "SmartDiag504 Taller"
    profile = (
        frappe.get_doc("Module Profile", profile_name)
        if frappe.db.exists("Module Profile", profile_name)
        else frappe.new_doc("Module Profile")
    )
    profile.module_profile_name = profile_name
    profile.set("block_modules", [])
    for module in frappe.get_all("Module Def", pluck="name"):
        if module not in ALLOWED_MODULES:
            profile.append("block_modules", {"module": module})
    profile.save(ignore_permissions=True)

    for user_name in DEMO_ADMIN_USERS:
        if not frappe.db.exists("User", user_name):
            continue
        user = frappe.get_doc("User", user_name)
        if user_meta.has_field("language"):
            user.language = "es"
        if user_meta.has_field("default_workspace"):
            user.default_workspace = "SmartDiag504"
        if user_meta.has_field("module_profile"):
            user.module_profile = profile_name
        current_roles = {row.role for row in user.roles}
        for role in DEMO_ADMIN_ROLES:
            if frappe.db.exists("Role", role) and role not in current_roles:
                user.append("roles", {"role": role})
        user.save(ignore_permissions=True)
    frappe.clear_cache()
    frappe.db.commit()
    return {
        "language": "es",
        "time_zone": "America/Tegucigalpa",
        "currency": "HNL",
        "workspace": "SmartDiag504",
    }


def _ensure_roles() -> None:
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def _ensure_workshop_permissions() -> None:
    """Agrega permisos operativos explícitos sin copiar permisos heredados inválidos."""
    for doctype, role_permissions in WORKSHOP_PERMISSIONS.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        for role, permission_types in role_permissions.items():
            filters = {"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0}
            permission_name = frappe.db.get_value("Custom DocPerm", filters, "name")
            permission = (
                frappe.get_doc("Custom DocPerm", permission_name)
                if permission_name
                else frappe.get_doc(
                    {
                        "doctype": "Custom DocPerm",
                        "parent": doctype,
                        "parenttype": "DocType",
                        "parentfield": "permissions",
                        "role": role,
                        "permlevel": 0,
                        "if_owner": 0,
                    }
                )
            )
            for permission_type in permission_types:
                permission.set(permission_type, 1)
            if permission.is_new():
                permission.insert(ignore_permissions=True)
            else:
                permission.save(ignore_permissions=True)
        frappe.clear_cache(doctype=doctype)


def _ensure_item_groups() -> None:
    for group_name, parent in (("Workshop Services", "All Item Groups"), ("Workshop Parts", "All Item Groups")):
        if not frappe.db.exists("Item Group", group_name):
            frappe.get_doc(
                {
                    "doctype": "Item Group",
                    "item_group_name": group_name,
                    "parent_item_group": parent,
                    "is_group": 0,
                }
            ).insert(ignore_permissions=True)


def after_install() -> None:
    _ensure_roles()
    _ensure_workshop_permissions()
    _ensure_item_groups()
    install_custom_fields()
    configure_smartdiag_site()
    frappe.db.commit()


def after_migrate() -> None:
    _ensure_roles()
    _ensure_workshop_permissions()
    install_custom_fields()
    configure_smartdiag_site()
