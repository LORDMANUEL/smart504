#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    ".mypy_cache",
    ".ruff_cache",
}
REQUIRED_ENV = {
    "COMPOSE_PROJECT_NAME",
    "ENVIRONMENT",
    "PUBLIC_SITE_ADDRESS",
    "OPS_SITE_ADDRESS",
    "API_SITE_ADDRESS",
    "ERP_SITE_ADDRESS",
    "ERP_SITE_NAME",
    "ERP_ADMIN_PASSWORD",
    "MARIADB_ROOT_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "ADMIN_API_TOKEN",
    "EVENT_HMAC_SECRET",
    "CHAT_SESSION_SECRET",
    "AI_GATEWAY_INTERNAL_TOKEN",
    "FRAPPE_API_KEY",
    "FRAPPE_API_SECRET",
    "RESTIC_PASSWORD",
    "GRAFANA_ADMIN_PASSWORD",
    "LLM_PROVIDER",
    "MEDIA_BACKEND",
}
REQUIRED_SERVICES = {
    "caddy",
    "haproxy",
    "public-web-a",
    "public-web-b",
    "ops-web-a",
    "ops-web-b",
    "platform-migrate",
    "platform-seed",
    "platform-api-a",
    "platform-api-b",
    "ai-gateway-a",
    "ai-gateway-b",
    "heartbeat-a",
    "heartbeat-b",
    "alerts-worker-a",
    "alerts-worker-b",
    "postgres",
    "redis-platform",
    "chromadb",
    "mariadb",
    "redis-cache",
    "redis-queue",
    "frappe-configurator",
    "frappe-site-init",
    "frappe-backend",
    "frappe-frontend",
    "frappe-websocket",
    "frappe-queue-short",
    "frappe-queue-long",
    "frappe-scheduler",
    "backup-runner",
}
ONE_SHOT_SERVICES = {"platform-migrate", "platform-seed", "frappe-configurator", "frappe-site-init"}
PRIVATE_SERVICES = {
    "postgres",
    "redis-platform",
    "chromadb",
    "mariadb",
    "redis-cache",
    "redis-queue",
    "ai-gateway-a",
    "ai-gateway-b",
}
FORBIDDEN_SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "OpenAI-style live key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}


def iter_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.parts)
    ]


def parse_structured_files(files: list[Path]) -> tuple[int, int]:
    yaml_count = 0
    json_count = 0
    for path in files:
        if path.suffix in {".yaml", ".yml"}:
            yaml.safe_load(path.read_text(encoding="utf-8"))
            yaml_count += 1
        elif path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            json_count += 1
    return yaml_count, json_count


def parse_env_template() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Malformed .env.example line: {raw}")
        key, value = line.split("=", 1)
        if key in values:
            raise ValueError(f"Duplicate environment key: {key}")
        values[key] = value
    missing = REQUIRED_ENV - set(values)
    if missing:
        raise ValueError(f"Missing required environment keys: {sorted(missing)}")
    return values


def validate_compose() -> dict[str, Any]:
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose.get("services", {})
    missing = REQUIRED_SERVICES - set(services)
    if missing:
        raise ValueError(f"compose.yaml is missing services: {sorted(missing)}")
    for network in ("app", "data"):
        if compose.get("networks", {}).get(network, {}).get("internal") is not True:
            raise ValueError(f"Network {network} must be internal")
    for name in PRIVATE_SERVICES:
        if services[name].get("ports"):
            raise ValueError(f"Internal service {name} must not publish host ports")
    for name in REQUIRED_SERVICES - ONE_SHOT_SERVICES:
        if "healthcheck" not in services[name]:
            raise ValueError(f"Long-running service {name} has no healthcheck")
    for service_name, service in services.items():
        build = service.get("build")
        if isinstance(build, dict) and (dockerfile := build.get("dockerfile")):
            if not (ROOT / dockerfile).is_file():
                raise ValueError(f"Missing Dockerfile for {service_name}: {dockerfile}")
        for volume in service.get("volumes", []) or []:
            source = volume.split(":", 1)[0] if isinstance(volume, str) else None
            if source and source.startswith("./") and not (ROOT / source).exists():
                raise ValueError(f"Missing bind mount source for {service_name}: {source}")
    return compose


def validate_release_contract() -> None:
    required_files = [
        "apps/public-web/src/components/ChatWidget.tsx",
        "apps/public-web/public/brand/smartdiag504-logo.png",
        "apps/ops-web/public/brand/smartdiag504-logo.png",
        "scripts/fetch-public-assets.sh",
        "infra/frappe/patches/beveren/0001-v16-compat.patch",
        "infra/ha/two-node/README.md",
        "docs/CODEX_EXECUTION_GUIDE.md",
        "docs/testing/ACCEPTANCE_TESTS.md",
    ]
    missing = [path for path in required_files if not (ROOT / path).is_file()]
    if missing:
        raise ValueError(f"Release contract files missing: {missing}")
    widget = (ROOT / required_files[0]).read_text(encoding="utf-8")
    if "OPENAI_API_KEY" in widget or "AI_GATEWAY_INTERNAL_TOKEN" in widget:
        raise ValueError("Frontend chatbot contains a server-side credential name")
    patch = (ROOT / "infra/frappe/patches/beveren/0001-v16-compat.patch").read_text(encoding="utf-8")
    if "class ServiceOrder(SellingController)" not in patch:
        raise ValueError("Beveren v16 item-selection repair is not present")


def scan_for_secrets(files: list[Path]) -> None:
    findings: list[str] = []
    text_suffixes = {
        ".py", ".ts", ".tsx", ".js", ".html", ".css", ".md", ".yaml", ".yml",
        ".json", ".sh", ".toml", ".txt", ".cfg", "",
    }
    for path in files:
        if path.name == ".env" or path.suffix not in text_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in FORBIDDEN_SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: {label}")
    if findings:
        raise ValueError("Potential committed secrets detected:\n" + "\n".join(findings))


def validate_docker_compose_when_available() -> str:
    if shutil.which("docker") is None:
        return "skipped (Docker is not installed in this environment)"
    selected_env = ROOT / ".env" if (ROOT / ".env").exists() else ROOT / ".env.example"
    command = [
        "docker", "compose", "--env-file", str(selected_env), "-f", str(ROOT / "compose.yaml"),
        "config", "--quiet",
    ]
    subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return "passed"


def main() -> int:
    files = iter_files()
    yaml_count, json_count = parse_structured_files(files)
    env = parse_env_template()
    compose = validate_compose()
    validate_release_contract()
    scan_for_secrets(files)
    docker_status = validate_docker_compose_when_available()
    print(
        "Repository validation passed: "
        f"{len(files)} files, {yaml_count} YAML, {json_count} JSON, "
        f"{len(compose['services'])} services, {len(env)} environment keys; "
        f"docker compose config {docker_status}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError, subprocess.CalledProcessError) as exc:
        print(f"Repository validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
