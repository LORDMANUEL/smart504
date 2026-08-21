#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE=${1:-.env}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${ROOT_DIR}/.env.example" "${ENV_FILE}"
fi

python3 - "${ENV_FILE}" <<'PY'
from __future__ import annotations

from pathlib import Path
import secrets
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
frappe_admin = secrets.token_urlsafe(32)
values = {
    "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
    "REDIS_PASSWORD": secrets.token_urlsafe(32),
    "MARIADB_ROOT_PASSWORD": secrets.token_urlsafe(32),
    "FRAPPE_ADMIN_PASSWORD": frappe_admin,
    "ERP_ADMIN_PASSWORD": frappe_admin,
    "ADMIN_API_TOKEN": secrets.token_urlsafe(48),
    "EVENT_HMAC_SECRET": secrets.token_urlsafe(48),
    "CHAT_SESSION_SECRET": secrets.token_urlsafe(48),
    "AI_GATEWAY_INTERNAL_TOKEN": secrets.token_urlsafe(48),
    "WEBHOOK_SECRET": secrets.token_urlsafe(48),
    "INTERNAL_API_KEY": secrets.token_urlsafe(48),
    "S3_ACCESS_KEY": "GK" + secrets.token_hex(16).upper(),
    "S3_SECRET_KEY": secrets.token_urlsafe(48),
    "GARAGE_RPC_SECRET": secrets.token_hex(32),
    "GARAGE_ADMIN_TOKEN": secrets.token_urlsafe(48),
    "GARAGE_METRICS_TOKEN": secrets.token_urlsafe(48),
    "RESTIC_PASSWORD": secrets.token_urlsafe(40),
    "GRAFANA_ADMIN_PASSWORD": secrets.token_urlsafe(32),
    "FRAPPE_API_KEY": secrets.token_hex(10),
    "FRAPPE_API_SECRET": secrets.token_hex(24),
}

seen: set[str] = set()
lines: list[str] = []
for raw in text.splitlines():
    line = raw
    if "=" in line and not line.lstrip().startswith("#"):
        key, current = line.split("=", 1)
        seen.add(key)
        if key in values and current in {"", "__GENERATE__"}:
            line = f"{key}={values[key]}"
    lines.append(line)
for key, value in values.items():
    if key not in seen:
        lines.append(f"{key}={value}")
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
path.chmod(0o600)
if "__GENERATE__" in path.read_text(encoding="utf-8"):
    raise SystemExit("ERROR: unresolved __GENERATE__ placeholders remain")
print(f"Secrets generated in {path}")
PY
