#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
ENV_FILE=.env
INSTALL_DOCKER=0
OPEN_FIREWALL=0
LOCAL_AI=0
OBSERVABILITY=0
TEST_FAILOVER=0
SKIP_BUILD=0
SKIP_ASSETS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --install-docker) INSTALL_DOCKER=1; shift ;;
    --open-firewall) OPEN_FIREWALL=1; shift ;;
    --local-ai) LOCAL_AI=1; shift ;;
    --observability) OBSERVABILITY=1; shift ;;
    --test-failover) TEST_FAILOVER=1; shift ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --skip-assets) SKIP_ASSETS=1; shift ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/codex-vps-deploy.sh [options]
  --env-file FILE       Environment file (default .env)
  --install-docker      Bootstrap Debian/Ubuntu host and Docker first
  --open-firewall       With --install-docker, configure UFW for SSH/80/443
  --local-ai            Start Ollama and pull the configured local model
  --observability       Start Prometheus, Grafana and blackbox exporter
  --test-failover       Prove same-host A/B application replica failover
  --skip-build          Reuse already-built images
  --skip-assets         Do not prefetch licensed public photographs
USAGE
      exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; exit 2 ;;
  esac
done

if [[ ${INSTALL_DOCKER} -eq 1 ]]; then
  bootstrap=("${ROOT_DIR}/scripts/bootstrap-host.sh")
  [[ ${OPEN_FIREWALL} -eq 1 ]] && bootstrap+=(--open-firewall)
  "${bootstrap[@]}"
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  cp .env.example "${ENV_FILE}"
fi
"${ROOT_DIR}/scripts/generate-secrets.sh" "${ENV_FILE}"

python3 - "${ENV_FILE}" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
values: dict[str, str] = {}
for raw in path.read_text(encoding="utf-8").splitlines():
    if not raw or raw.lstrip().startswith("#") or "=" not in raw:
        continue
    key, value = raw.split("=", 1)
    values[key.strip()] = value.strip().strip('"').strip("'")
required = [
    "PUBLIC_SITE_ADDRESS", "CUSTOMER_SITE_ADDRESS", "OPS_SITE_ADDRESS",
    "API_SITE_ADDRESS", "ERP_SITE_ADDRESS", "ACME_EMAIL",
]
missing = [key for key in required if not values.get(key)]
if missing:
    raise SystemExit(f"ERROR: required environment values are missing: {', '.join(missing)}")
for key in required[:-1]:
    value = values[key]
    if re.search(r"localhost|example\\.(com|org|net)$", value, re.I):
        raise SystemExit(f"ERROR: {key} still contains a non-production host: {value}")
if values.get("BUSINESS_PHONE", "").endswith("0000-0000"):
    print("WARNING: BUSINESS_PHONE is still a placeholder; update it before publishing.", file=sys.stderr)
if values.get("BUSINESS_WHATSAPP_URL", "").endswith("50400000000"):
    print("WARNING: BUSINESS_WHATSAPP_URL is still a placeholder; update it before publishing.", file=sys.stderr)
PY

install_args=(--env-file "${ENV_FILE}")
[[ ${INSTALL_DOCKER} -eq 1 ]] || install_args+=(--skip-docker-install)
[[ ${LOCAL_AI} -eq 1 ]] && install_args+=(--local-ai)
[[ ${OBSERVABILITY} -eq 1 ]] && install_args+=(--observability)
[[ ${TEST_FAILOVER} -eq 1 ]] && install_args+=(--test-failover)
[[ ${SKIP_BUILD} -eq 1 ]] && install_args+=(--skip-build)
[[ ${SKIP_ASSETS} -eq 1 ]] && install_args+=(--skip-assets)

"${ROOT_DIR}/scripts/install-vps.sh" "${install_args[@]}"

cat <<REPORT
Codex VPS deployment workflow completed.
Environment file: ${ENV_FILE}
Runtime verification: scripts/smoke-test.sh
Detailed operator instructions: docs/deployment/VPS_RUNBOOK.md
Codex handoff prompt: docs/CODEX_VPS_DEPLOY_PROMPT.md
REPORT
