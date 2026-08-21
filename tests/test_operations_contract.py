from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_OPERATION_FILES = {
    "scripts/bootstrap-host.sh",
    "scripts/codex-vps-deploy.sh",
    "scripts/generate-secrets.sh",
    "scripts/fetch-public-assets.sh",
    "scripts/build-frontends.sh",
    "scripts/backup.sh",
    "scripts/verify-backup.sh",
    "scripts/restore.sh",
    "scripts/verify.sh",
    "scripts/capture-previews.sh",
    "scripts/package-release.sh",
    "scripts/validate_repository.py",
    "infra/monitoring/prometheus.yml",
    "infra/monitoring/blackbox.yml",
    "infra/monitoring/grafana/provisioning/datasources/prometheus.yml",
    "docs/deployment/VPS_RUNBOOK.md",
    "docs/security/THREAT_MODEL.md",
}


def test_operational_files_exist() -> None:
    missing = sorted(path for path in REQUIRED_OPERATION_FILES if not (ROOT / path).is_file())
    assert not missing, f"Missing operational files: {missing}"


def test_shell_scripts_are_fail_fast_and_restore_requires_explicit_confirmation() -> None:
    for path in sorted((ROOT / "scripts").glob("*.sh")):
        text = path.read_text(encoding="utf-8")
        assert text.startswith("#!/usr/bin/env bash"), f"{path.name} needs a portable bash shebang"
        assert "set -Eeuo pipefail" in text, f"{path.name} must fail fast"

    restore = (ROOT / "scripts" / "restore.sh").read_text(encoding="utf-8")
    assert "RESTORE-SMARTDIAG504" in restore
    assert "--confirm" in restore
    assert "manifest.sha256" in restore

    backup = (ROOT / "infra" / "backup" / "run-backup.sh").read_text(encoding="utf-8")
    assert "manifest.sha256" in backup
    assert "pg_dump" in backup
    assert "mariadb-dump" in backup
    assert "frappe-sites.tar.zst" in backup
    assert "platform-media.tar.zst" in backup
    assert "restic" in backup.casefold()


def test_monitoring_stack_is_private_and_profile_gated() -> None:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose["services"]
    for name in ("blackbox-exporter", "prometheus", "grafana"):
        assert name in services
        assert "observability" in services[name].get("profiles", [])
        assert "healthcheck" in services[name]
    assert services["prometheus"]["ports"][0].startswith("127.0.0.1:")
    assert services["grafana"]["ports"][0].startswith("127.0.0.1:")


def test_prometheus_probes_balanced_product_health_endpoints() -> None:
    config = yaml.safe_load((ROOT / "infra" / "monitoring" / "prometheus.yml").read_text(encoding="utf-8"))
    targets = {
        target
        for job in config["scrape_configs"]
        for group in job.get("static_configs", [])
        for target in group.get("targets", [])
    }
    assert "http://haproxy:8082/health" in targets
    assert "http://haproxy:8083/health" in targets
    assert "http://haproxy:8080/healthz" in targets
    assert "http://haproxy:8081/healthz" in targets
    assert "http://frappe-frontend:8080/api/method/ping" in targets


def test_secret_generator_fills_v04_security_contract(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    script_path = ROOT / "scripts" / "generate-secrets.sh"
    if os.name == "nt":
        script_arg = f"/mnt/{script_path.drive[0].lower()}{script_path.as_posix()[2:]}"
        env_arg = f"/mnt/{env_file.drive[0].lower()}{env_file.as_posix()[2:]}"
    else:
        script_arg = str(script_path)
        env_arg = str(env_file)
    subprocess.run(
        ["bash", script_arg, env_arg],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    values: dict[str, str] = {}
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key] = value
    for key in (
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "MARIADB_ROOT_PASSWORD",
        "ADMIN_API_TOKEN",
        "EVENT_HMAC_SECRET",
        "CHAT_SESSION_SECRET",
        "AI_GATEWAY_INTERNAL_TOKEN",
        "GRAFANA_ADMIN_PASSWORD",
    ):
        assert len(values[key]) >= 24
    assert "__GENERATE__" not in env_file.read_text(encoding="utf-8")
    if os.name != "nt":
        assert env_file.stat().st_mode & 0o777 == 0o600


def test_vps_installer_is_full_stack_and_codex_entrypoint_is_non_interactive_safe() -> None:
    installer = (ROOT / "scripts" / "install-vps.sh").read_text(encoding="utf-8")
    assert "--skip-erp" not in installer
    assert "frappe-configurator" in installer
    assert "frappe-site-init" in (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "scripts/wait-ready.sh" in installer
    assert "scripts/smoke-test.sh" in installer

    codex = (ROOT / "scripts" / "codex-vps-deploy.sh").read_text(encoding="utf-8")
    assert "--install-docker" in codex
    assert "--env-file" in codex
    assert "install-vps.sh" in codex
    assert "CODEX_VPS_DEPLOY_PROMPT.md" in (ROOT / "docs" / "CODEX_VPS_DEPLOY_PROMPT.md").read_text(encoding="utf-8")


def test_release_packager_uses_v04_root_and_safe_exclusions() -> None:
    text = (ROOT / "scripts" / "package-release.sh").read_text(encoding="utf-8")
    assert "0.4.0" in text
    assert "smartdiag504_platform_complete_v" in text
    assert "smartdiag504-platform-v" in text
    for sensitive in (".env", ".git", "node_modules", "__pycache__"):
        assert sensitive in text


def test_backup_and_restore_cover_object_storage_state() -> None:
    backup = (ROOT / "infra" / "backup" / "run-backup.sh").read_text(encoding="utf-8")
    restore = (ROOT / "scripts" / "restore.sh").read_text(encoding="utf-8")
    verifier = (ROOT / "scripts" / "verify-backup.sh").read_text(encoding="utf-8")
    for artifact in ("garage-config.tar.zst", "garage-meta.tar.zst", "garage-data.tar.zst"):
        assert artifact in backup
        assert artifact in restore
        assert artifact in verifier
