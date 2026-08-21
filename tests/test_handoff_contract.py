from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_HANDOFF_FILES = {
    ".github/workflows/ci.yml",
    ".github/workflows/build-images.yml",
    "docs/testing/ACCEPTANCE_TESTS.md",
    "docs/testing/VERIFICATION_REPORT.md",
    "docs/CODEX_EXECUTION_GUIDE.md",
    "docs/CODEX_VPS_DEPLOY_PROMPT.md",
    "docs/ux/SCREEN_INVENTORY.md",
    "docs/licensing/THIRD_PARTY.md",
    "docs/backlog/EPICS.md",
    "docs/architecture/DATA_OWNERSHIP.md",
    "SMARTDIAG504_IMPLEMENTATION_MASTER.md",
    "MANIFEST.sha256",
}


def test_handoff_files_exist() -> None:
    missing = sorted(path for path in REQUIRED_HANDOFF_FILES if not (ROOT / path).is_file())
    assert not missing, f"Missing handoff files: {missing}"


def test_ci_runs_full_repository_verification_and_image_builds() -> None:
    ci = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    ci_text = str(ci)
    assert "scripts/verify.sh" in ci_text
    assert "playwright" in ci_text.casefold()
    assert "typescript@5.8.3" in ci_text

    builds = yaml.safe_load((ROOT / ".github" / "workflows" / "build-images.yml").read_text(encoding="utf-8"))
    build_text = str(builds)
    for image in ("public-web", "ops-web", "platform-api", "ai-gateway", "alerts-worker", "frappe-workshop"):
        assert image in build_text
    assert "build-push-action" in build_text


def test_acceptance_suite_covers_end_to_end_workshop_and_recovery() -> None:
    text = (ROOT / "docs" / "testing" / "ACCEPTANCE_TESTS.md").read_text(encoding="utf-8").casefold()
    required_terms = {
        "crear cliente",
        "registrar vehículo",
        "recibir vehículo",
        "abrir ot",
        "diagnóstico",
        "aprobar parcialmente",
        "dos técnicos",
        "devolver sobrantes",
        "control de calidad",
        "generar factura",
        "cerrar caja",
        "historial por vin",
        "garantía",
        "restauración",
        "idempotencia",
    }
    missing = sorted(term for term in required_terms if term not in text)
    assert not missing, f"Acceptance coverage gaps: {missing}"


def test_codex_guide_preserves_system_boundaries() -> None:
    text = (ROOT / "docs" / "CODEX_EXECUTION_GUIDE.md").read_text(encoding="utf-8")
    assert "ERPNext" in text
    assert "Service Order" in text
    assert "no crear una segunda OT" in text
    assert "TDD" in text
    assert "Gate" in text
    assert "adaptador Frappe" in text


def test_readme_documents_embedded_chatbot_and_one_command_vps_handoff() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "chatbot" in text.casefold()
    assert "scripts/codex-vps-deploy.sh" in text
    assert "scripts/install-vps.sh" in text
    assert "CREATED" in text
    assert "INVOICED" in text


def test_container_build_workflow_provides_frappe_apps_manifest_secret() -> None:
    text = (ROOT / ".github/workflows/build-images.yml").read_text(encoding="utf-8")
    assert "secret-files:" in text
    assert "apps_json=./infra/frappe/apps.json" in text
