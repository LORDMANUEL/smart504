from __future__ import annotations

import frappe

# Preserve the original API principal so existing deployments can rotate the
# secret without creating a second integration identity.
INTEGRATION_USER = "smartdiag.integration@smartdiag504.local"
ROLE_NAME = "SmartDiag Integration API"
READ_DOCTYPES = [
    "Sales Invoice",
    "Item",
    "Item Price",
    "Item Group",
    "Bin",
    "Warehouse",
    "Customer",
    "Company",
    "Price List",
    "Service Order",
    "SmartDiag Vehicle",
]


def ensure_integration_user(api_key: str | None = None, api_secret: str | None = None) -> dict[str, str]:
    if not frappe.db.exists("Role", ROLE_NAME):
        frappe.get_doc({"doctype": "Role", "role_name": ROLE_NAME, "desk_access": 0}).insert(
            ignore_permissions=True
        )

    for doctype in READ_DOCTYPES:
        exists = frappe.db.exists(
            "Custom DocPerm", {"parent": doctype, "role": ROLE_NAME, "permlevel": 0}
        )
        if not exists:
            frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": doctype,
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": ROLE_NAME,
                    "permlevel": 0,
                    "read": 1,
                    "select": 1,
                    "report": 1,
                }
            ).insert(ignore_permissions=True)

    if not frappe.db.exists("User", INTEGRATION_USER):
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": INTEGRATION_USER,
                "first_name": "SmartDiag",
                "last_name": "Integration",
                "enabled": 1,
                "user_type": "System User",
                "send_welcome_email": 0,
                "roles": [{"role": ROLE_NAME}],
            }
        )
        user.insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", INTEGRATION_USER)
        if ROLE_NAME not in {row.role for row in user.roles}:
            user.append("roles", {"role": ROLE_NAME})

    if api_key:
        user.api_key = api_key
    if api_secret:
        user.api_secret = api_secret
    user.save(ignore_permissions=True)
    frappe.db.commit()
    return {"user": INTEGRATION_USER, "role": ROLE_NAME}
