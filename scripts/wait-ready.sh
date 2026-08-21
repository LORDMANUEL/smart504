#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE=${1:-.env}
TIMEOUT=${2:-600}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck source=scripts/lib/common.sh
source "${ROOT_DIR}/scripts/lib/common.sh"
smartdiag_require_env_file "${ENV_FILE}"
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a
API_BASE=$(smartdiag_url "${SMOKE_API_URL:-${API_SITE_ADDRESS:-http://localhost:8082}}")
START=$(date +%s)
while true; do
  if curl -fsS --max-time 10 "${API_BASE}/ready" >/dev/null 2>&1; then
    echo "Platform API is ready at ${API_BASE}"
    break
  fi
  if (( $(date +%s) - START > TIMEOUT )); then
    docker compose --env-file "${ENV_FILE}" -f compose.yaml ps || true
    docker compose --env-file "${ENV_FILE}" -f compose.yaml logs --tail=150 \
      platform-api-a platform-api-b platform-migrate platform-seed ai-gateway-a ai-gateway-b || true
    echo "ERROR: timed out waiting for platform readiness at ${API_BASE}" >&2
    exit 1
  fi
  sleep 3
done
