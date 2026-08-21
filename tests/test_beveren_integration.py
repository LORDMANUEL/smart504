import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFRA = ROOT / "infra" / "frappe"
PATCH = INFRA / "patches" / "beveren" / "0001-v16-compat.patch"
STATUS = INFRA / "BEVEREN_PATCH_STATUS.md"
CONTAINERFILE = INFRA / "Containerfile"
APPS_JSON = INFRA / "apps.json"


def test_beveren_is_pinned_and_patch_is_registered() -> None:
    status = STATUS.read_text(encoding="utf-8")
    commit_match = re.search(r"Upstream commit:\s*`([0-9a-f]{40})`", status)
    checksum_match = re.search(r"Patch SHA256:\s*`([0-9a-f]{64})`", status)
    assert commit_match
    assert checksum_match
    assert hashlib.sha256(PATCH.read_bytes()).hexdigest() == checksum_match.group(1)
    assert "Issue #24" in status and "integration gate" in status.lower()


def test_v16_patch_contains_required_compatibility_repairs() -> None:
    patch = PATCH.read_text(encoding="utf-8")
    assert 'required_apps = ["erpnext"]' in patch
    assert "[tool.bench.frappe-dependencies]" in patch
    assert 'frappe = ">=16.0.0,<17.0.0"' in patch
    assert "frappe.contacts.doctype.address.address.address_query" in patch
    assert "frappe.contacts.doctype.contact.contact.contact_query" in patch
    assert "from erpnext.controllers.selling_controller import SellingController" in patch
    assert "class ServiceOrder(SellingController)" in patch


def test_custom_frappe_image_fetches_pinned_beveren_and_local_app() -> None:
    content = CONTAINERFILE.read_text(encoding="utf-8")
    assert "ARG BEVEREN_REF=ab6d56d1069882326475f256d09cc63236eddec1" in content
    assert "git checkout --detach ${BEVEREN_REF}" in content
    assert "git apply /tmp/0001-v16-compat.patch" in content
    assert "COPY --chown=frappe:frappe frappe-apps/smartdiag_workshop" in content
    assert "COPY --chown=frappe:frappe packages/smartdiag_domain" in content
    assert "bench build --app beveren_fsm --app smartdiag_workshop" in content


def test_apps_json_pins_erpnext_release_tag() -> None:
    apps = json.loads(APPS_JSON.read_text(encoding="utf-8"))
    assert apps == [{"url": "https://github.com/frappe/erpnext", "branch": "v16.32.0"}]
