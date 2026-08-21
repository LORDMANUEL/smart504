import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frappe-apps" / "smartdiag_workshop"
PACKAGE = APP / "smartdiag_workshop"
DOCTYPE_ROOT = PACKAGE / "smartdiag_workshop" / "doctype"

EXPECTED_DOCTYPES = {
    "smartdiag_vehicle": "SmartDiag Vehicle",
    "vehicle_check_in": "Vehicle Check In",
    "vehicle_check_in_photo": "Vehicle Check In Photo",
    "diagnostic_session": "Diagnostic Session",
    "diagnostic_finding": "Diagnostic Finding",
    "workshop_bay": "Workshop Bay",
    "bay_assignment": "Bay Assignment",
    "labor_operation": "Labor Operation",
    "technician_assignment": "Technician Assignment",
    "part_request": "Part Request",
    "part_request_item": "Part Request Item",
    "workshop_quality_check": "Workshop Quality Check",
    "quality_check_item": "Quality Check Item",
    "workshop_warranty_claim": "Workshop Warranty Claim",
    "maintenance_recommendation": "Maintenance Recommendation",
    "smartdiag_event_outbox": "SmartDiag Event Outbox",
    "smartdiag_settings": "SmartDiag Settings",
    "vehicle_fitment": "Vehicle Fitment",
}


def test_frappe_app_declares_required_apps() -> None:
    hooks = (PACKAGE / "hooks.py").read_text(encoding="utf-8")
    assert 'required_apps = ["erpnext", "beveren_fsm"]' in hooks
    assert 'after_install = "smartdiag_workshop.setup.install.after_install"' in hooks


def test_all_required_doctypes_exist_and_match_name() -> None:
    missing: list[str] = []
    for folder, expected_name in EXPECTED_DOCTYPES.items():
        path = DOCTYPE_ROOT / folder / f"{folder}.json"
        if not path.exists():
            missing.append(str(path.relative_to(ROOT)))
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["name"] == expected_name
        assert data["doctype"] == "DocType"
        assert isinstance(data.get("fields"), list)
    assert not missing, f"Missing DocTypes: {missing}"


def test_vehicle_has_unique_vin_and_customer() -> None:
    data = json.loads(
        (DOCTYPE_ROOT / "smartdiag_vehicle" / "smartdiag_vehicle.json").read_text(encoding="utf-8")
    )
    fields = {field["fieldname"]: field for field in data["fields"]}
    assert fields["vin"]["unique"] == 1
    assert fields["vin"]["reqd"] == 1
    assert fields["customer"]["options"] == "Customer"


def test_service_order_extensions_are_prefixed() -> None:
    module = (PACKAGE / "setup" / "custom_fields.py").read_text(encoding="utf-8")
    for fieldname in ("sd_vehicle", "sd_check_in", "sd_promised_at", "sd_workshop_bay"):
        assert f'"fieldname": "{fieldname}"' in module


def test_doctype_controller_class_names_match_frappe_resolution() -> None:
    expected = {
        "smartdiag_vehicle": "SmartDiagVehicle",
        "smartdiag_event_outbox": "SmartDiagEventOutbox",
        "smartdiag_settings": "SmartDiagSettings",
    }
    for folder, class_name in expected.items():
        module = (DOCTYPE_ROOT / folder / f"{folder}.py").read_text(encoding="utf-8")
        assert f"class {class_name}(Document):" in module


def test_service_order_event_imports_and_enforces_official_transition(monkeypatch) -> None:
    fake_frappe = ModuleType("frappe")

    def throw(message: str) -> None:
        raise ValueError(message)

    fake_frappe.throw = throw
    fake_frappe.session = SimpleNamespace(user="advisor@smartdiag.test")
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    monkeypatch.syspath_prepend(str(APP))
    monkeypatch.syspath_prepend(str(ROOT / "packages" / "smartdiag_domain"))
    sys.modules.pop("smartdiag_workshop.events.service_order", None)

    module = importlib.import_module("smartdiag_workshop.events.service_order")

    class Doc(dict):
        doctype = "Service Order"
        name = "SO-0001"

        def get_doc_before_save(self):
            return self.get("_before")

        def has_value_changed(self, fieldname: str) -> bool:
            before = self.get("_before") or {}
            return before.get(fieldname) != self.get(fieldname)

    created = Doc(sd_vehicle="VEH-1", sd_workflow_state=None)
    module.validate_service_order(created)
    assert created["sd_workflow_state"] == "CREATED"

    quoted = Doc(
        sd_vehicle="VEH-1",
        sd_workflow_state="QUOTED_BY_TECHNICIAN",
        sd_transition_reason="Diagnostico y tiempos registrados",
        _before={"sd_workflow_state": "CREATED"},
    )
    module.validate_service_order(quoted)

    invalid = Doc(
        sd_vehicle="VEH-1",
        sd_workflow_state="INVOICED",
        sd_transition_reason="Salto no permitido",
        _before={"sd_workflow_state": "CREATED"},
    )
    with pytest.raises(ValueError, match="not allowed"):
        module.validate_service_order(invalid)
