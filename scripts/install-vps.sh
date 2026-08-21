#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
ENV_FILE=${ENV_FILE:-.env}
SKIP_BUILD=0
SKIP_ASSETS=0
SKIP_DOCKER_INSTALL=0
ENABLE_LOCAL_AI=0
ENABLE_OBSERVABILITY=0
TEST_FAILOVER=0
ALLOW_LOW_RESOURCES=${SMARTDIAG_ALLOW_LOW_RESOURCES:-0}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --skip-assets) SKIP_ASSETS=1; shift ;;
    --skip-docker-install) SKIP_DOCKER_INSTALL=1; shift ;;
    --local-ai) ENABLE_LOCAL_AI=1; shift ;;
    --observability) ENABLE_OBSERVABILITY=1; shift ;;
    --test-failover) TEST_FAILOVER=1; shift ;;
    --allow-low-resources) ALLOW_LOW_RESOURCES=1; shift ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/install-vps.sh [options]
  --env-file FILE          Environment file (default .env)
  --skip-build             Reuse existing local images
  --skip-assets            Do not prefetch public licensed photographs
  --skip-docker-install    Fail instead of installing Docker on Debian/Ubuntu
  --local-ai               Start Ollama profile and route chatbot through it
  --observability          Start Prometheus, Grafana and blackbox exporter
  --test-failover          Stop application replica A and prove B remains available
  --allow-low-resources    Continue below recommended RAM/disk thresholds
USAGE
      exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; exit 2 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  if [[ ${SKIP_DOCKER_INSTALL} -eq 1 ]]; then
    echo "ERROR: Docker Engine 23+ and Compose v2 are required." >&2
    exit 1
  fi
  "${ROOT_DIR}/scripts/install-docker.sh"
fi
for command_name in curl python3 git unzip; do
  command -v "${command_name}" >/dev/null 2>&1 || { echo "ERROR: ${command_name} is required." >&2; exit 1; }
done
docker info >/dev/null 2>&1 || {
  echo "ERROR: current user cannot access Docker. Run as root or start a new login after joining the docker group." >&2
  exit 1
}

memory_mb=$(awk '/MemTotal:/ {print int($2/1024)}' /proc/meminfo)
disk_mb=$(df -Pm "${ROOT_DIR}" | awk 'NR==2 {print $4}')
minimum_memory=7500
[[ ${ENABLE_LOCAL_AI} -eq 0 ]] || minimum_memory=15000
if (( memory_mb < minimum_memory || disk_mb < 30000 )); then
  message="Host resources below recommended minimum: RAM=${memory_mb}MB (required ${minimum_memory}MB), free disk=${disk_mb}MB (required 30000MB)."
  if [[ ${ALLOW_LOW_RESOURCES} -eq 1 ]]; then
    echo "WARNING: ${message}" >&2
  else
    echo "ERROR: ${message} Use --allow-low-resources only for controlled staging." >&2
    exit 1
  fi
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  cp .env.example "${ENV_FILE}"
  echo "Created ${ENV_FILE}. Review DNS, contact data, fiscal settings and offsite backup destination before production use."
fi
"${ROOT_DIR}/scripts/generate-secrets.sh" "${ENV_FILE}"
if grep -q '__GENERATE__' "${ENV_FILE}"; then
  echo "ERROR: unresolved secret placeholders remain in ${ENV_FILE}." >&2
  exit 1
fi

python3 - "${ENV_FILE}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
values = {}
for raw in path.read_text(encoding="utf-8").splitlines():
    if not raw or raw.lstrip().startswith("#") or "=" not in raw:
        continue
    key, value = raw.split("=", 1)
    values[key.strip()] = value.strip().strip('"').strip("'")
required = [
    "PUBLIC_SITE_ADDRESS", "CUSTOMER_SITE_ADDRESS", "OPS_SITE_ADDRESS",
    "API_SITE_ADDRESS", "ERP_SITE_ADDRESS", "FRAPPE_SITE_NAME", "ACME_EMAIL",
    "POSTGRES_PASSWORD", "MARIADB_ROOT_PASSWORD", "ADMIN_API_TOKEN",
    "EVENT_HMAC_SECRET", "CHAT_SESSION_SECRET", "AI_GATEWAY_INTERNAL_TOKEN",
    "FRAPPE_API_KEY", "FRAPPE_API_SECRET",
]
missing = [key for key in required if not values.get(key)]
if missing:
    raise SystemExit(f"ERROR: missing required configuration: {', '.join(missing)}")
if values["FRAPPE_SITE_NAME"] != values["ERP_SITE_ADDRESS"]:
    raise SystemExit("ERROR: FRAPPE_SITE_NAME and ERP_SITE_ADDRESS must match for the single-site deployment")
PY

if [[ ${SKIP_ASSETS} -eq 0 ]]; then
  if ! "${ROOT_DIR}/scripts/fetch-public-assets.sh"; then
    echo "WARNING: photographs could not be prefetched; the web keeps verified remote fallbacks. Retry scripts/fetch-public-assets.sh before go-live." >&2
  fi
fi

profiles=()
if [[ ${ENABLE_LOCAL_AI} -eq 1 ]]; then
  profiles+=(--profile local-ai)
  export LLM_PROVIDER=ollama
fi
if [[ ${ENABLE_OBSERVABILITY} -eq 1 ]]; then
  profiles+=(--profile observability)
fi
compose=(docker compose --env-file "${ENV_FILE}" "${profiles[@]}" -f compose.yaml)
"${compose[@]}" config --quiet

if [[ ${SKIP_BUILD} -eq 0 ]]; then
  "${compose[@]}" build \
    public-web-a ops-web-a platform-migrate ai-gateway-a heartbeat-a alerts-worker-a \
    backup-runner frappe-configurator
fi

"${compose[@]}" up -d

# First prove internal services before depending on external DNS/TLS.
for attempt in $(seq 1 120); do
  if "${compose[@]}" exec -T platform-api-a curl -fsS http://127.0.0.1:8000/ready >/dev/null 2>&1 \
    && "${compose[@]}" exec -T ai-gateway-a curl -fsS http://127.0.0.1:8000/ready >/dev/null 2>&1; then
    break
  fi
  if [[ ${attempt} -eq 120 ]]; then
    "${compose[@]}" ps || true
    "${compose[@]}" logs --tail=200 platform-api-a ai-gateway-a platform-migrate platform-seed || true
    echo "ERROR: internal application readiness timed out." >&2
    exit 1
  fi
  sleep 3
done

"${ROOT_DIR}/scripts/wait-ready.sh" "${ENV_FILE}" 1200
"${ROOT_DIR}/scripts/smoke-test.sh" "${ENV_FILE}"
if [[ ${TEST_FAILOVER} -eq 1 ]]; then
  "${ROOT_DIR}/scripts/ha-smoke-test.sh" "${ENV_FILE}"
fi

public_address=$(awk -F= '$1=="PUBLIC_SITE_ADDRESS" {print substr($0,index($0,"=")+1)}' "${ENV_FILE}")
ops_address=$(awk -F= '$1=="OPS_SITE_ADDRESS" {print substr($0,index($0,"=")+1)}' "${ENV_FILE}")
erp_address=$(awk -F= '$1=="ERP_SITE_ADDRESS" {print substr($0,index($0,"=")+1)}' "${ENV_FILE}")
cat <<REPORT
SmartDiag504 v0.4.0 deployment completed and smoke-tested.
Public site: https://${public_address#http://}
Operations: https://${ops_address#http://}
ERPNext: https://${erp_address#http://}

Required production gates still outside this installer: Honduras fiscal approval, payment gateway certification, offsite backup restore drill, penetration test and physical two-VPS HA acceptance when that topology is required.
REPORT
