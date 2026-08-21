#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
RUNTIME=0
SKIP_BROWSER=0
REQUIRE_FRONTEND_DEPS=0
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/.env}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --runtime) RUNTIME=1; shift ;;
    --skip-browser) SKIP_BROWSER=1; shift ;;
    --require-frontend-deps) REQUIRE_FRONTEND_DEPS=1; shift ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--runtime] [--skip-browser] [--require-frontend-deps] [--env-file FILE]"
      exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
  esac
done

python3 scripts/validate_repository.py
bash scripts/fetch-public-assets.sh --check
if [[ ${REQUIRE_FRONTEND_DEPS} -eq 1 ]]; then
  bash scripts/build-frontends.sh --check --require-deps
else
  bash scripts/build-frontends.sh --check
fi

PYTHONPATH="${ROOT_DIR}/packages/smartdiag_domain" \
  python3 -m pytest -q packages/smartdiag_domain/tests
rm -f /tmp/smartdiag504-platform-api-tests/test.db
PYTHONPATH="${ROOT_DIR}/packages/smartdiag_domain:${ROOT_DIR}/services/platform-api" \
  python3 -m pytest -q services/platform-api/tests
PYTHONPATH="${ROOT_DIR}/services/ai-gateway" \
  python3 -m pytest -q services/ai-gateway/tests
PYTHONPATH="${ROOT_DIR}/services/alerts-worker" \
  python3 -m pytest -q services/alerts-worker/tests
python3 -m pytest -q \
  tests/test_repository_contract.py \
  tests/test_design_system_contract.py \
  tests/test_frappe_app_contract.py \
  tests/test_platform_settings.py \
  tests/test_beveren_integration.py \
  tests/test_compose_contract.py \
  tests/test_operations_contract.py \
  tests/test_chatbot_release_contract.py \
  tests/test_handoff_contract.py

if [[ ${SKIP_BROWSER} -eq 0 ]]; then
  python3 -m pytest -q tests/test_public_web_browser.py tests/test_ops_web_browser.py
fi

python3 -m compileall -q packages services frappe-apps scripts
find scripts -type f -name '*.sh' -print0 | xargs -0 -n1 bash -n

echo "Static verification passed."

if command -v docker >/dev/null 2>&1; then
  selected_env="${ENV_FILE}"
  [[ -f "${selected_env}" ]] || selected_env="${ROOT_DIR}/.env.example"
  docker compose --env-file "${selected_env}" -f compose.yaml config --quiet
  docker compose -f compose.preview.yaml config --quiet
  echo "Docker Compose configuration passed."
else
  echo "Docker Compose runtime validation skipped: docker is not installed in this environment."
fi

if [[ ${RUNTIME} -eq 1 ]]; then
  [[ -f "${ENV_FILE}" ]] || { echo "ERROR: runtime verification requires ${ENV_FILE}." >&2; exit 1; }
  command -v docker >/dev/null 2>&1 || { echo "ERROR: runtime verification requires Docker." >&2; exit 1; }
  command -v curl >/dev/null 2>&1 || { echo "ERROR: runtime verification requires curl." >&2; exit 1; }

  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
  compose=(docker compose --env-file "${ENV_FILE}" -f compose.yaml)
  required=(
    caddy haproxy public-web-a public-web-b ops-web-a ops-web-b
    platform-api-a platform-api-b ai-gateway-a ai-gateway-b
    heartbeat-a heartbeat-b alerts-worker-a alerts-worker-b
    mariadb postgres redis-platform garage frappe-backend frappe-frontend
  )
  running="$("${compose[@]}" ps --status running --services)"
  for service in "${required[@]}"; do
    grep -qx "${service}" <<<"${running}" || { echo "ERROR: ${service} is not running." >&2; exit 1; }
  done

  "${ROOT_DIR}/scripts/smoke-test.sh" "${ENV_FILE}"
  echo "Runtime verification passed."
fi
