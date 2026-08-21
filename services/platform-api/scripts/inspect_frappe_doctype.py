"""Print the required and SmartDiag fields of a Frappe DocType without secrets."""

from __future__ import annotations

import argparse

from app.config import get_settings
from app.services.frappe import FrappeReadClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("doctype")
    args = parser.parse_args()
    document = FrappeReadClient(get_settings()).get_resource("DocType", args.doctype)
    fields = [
        {
            "fieldname": field.get("fieldname"),
            "fieldtype": field.get("fieldtype"),
            "options": field.get("options"),
            "required": bool(field.get("reqd")),
        }
        for field in document.get("fields", [])
        if field.get("reqd") or str(field.get("fieldname") or "").startswith("sd_")
    ]
    print({"doctype": args.doctype, "fields": fields})


if __name__ == "__main__":
    main()
