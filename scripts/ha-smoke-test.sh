#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE=${1:-.env}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck source=scripts/lib/common.sh
source "${ROOT_DIR}/scripts/lib/common.sh"
smartdiag_require_env_file "${ENV_FILE}"
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a
COMPOSE=(docker compose --env-file "${ENV_FILE}" -f compose.yaml)
API_BASE=$(smartdiag_url "${SMOKE_API_URL:-${API_SITE_ADDRESS:-http://localhost:8082}}")
PUBLIC_BASE=$(smartdiag_url "${SMOKE_BASE_URL:-${PUBLIC_SITE_ADDRESS:-http://localhost}}")

cleanup() {
  "${COMPOSE[@]}" start platform-api-a public-web-a >/dev/null 2>&1 || true
}
trap cleanup EXIT

curl -fsS --max-time 15 "${API_BASE}/health" >/dev/null
"${COMPOSE[@]}" stop platform-api-a
for _ in $(seq 1 30); do
  curl -fsS --max-time 5 "${API_BASE}/health" >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS --max-time 15 "${API_BASE}/health" | python3 -c 'import json,sys; assert json.load(sys.stdin)["status"]=="ok"'

"${COMPOSE[@]}" stop public-web-a
for _ in $(seq 1 30); do
  curl -fsS --max-time 5 "${PUBLIC_BASE}/" >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS --max-time 15 "${PUBLIC_BASE}/" | grep -qi SmartDiag504

"${COMPOSE[@]}" start platform-api-a public-web-a
for _ in $(seq 1 45); do
  if "${COMPOSE[@]}" ps --status running --services | grep -qx platform-api-a; then
    break
  fi
  sleep 1
done

echo "Single-VPS replica failover passed: API and public web remained available while replica A was stopped."
echo "This test covers container/service failure, not loss of the complete VPS. Two-host failover requires the optional infra/ha/two-node design and database replication."
