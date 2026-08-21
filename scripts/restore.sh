#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
ENV_FILE=${ENV_FILE:-.env}
ARCHIVE=""
CONFIRM=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --archive) ARCHIVE="$2"; shift 2 ;;
    --confirm) CONFIRM="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --archive FILE --confirm RESTORE-SMARTDIAG504 [--env-file FILE]"
      exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; exit 2 ;;
  esac
done

[[ "${CONFIRM}" == "RESTORE-SMARTDIAG504" ]] || { echo "ERROR: destructive restore requires --confirm RESTORE-SMARTDIAG504" >&2; exit 2; }
[[ -f "${ENV_FILE}" ]] || { echo "ERROR: missing ${ENV_FILE}." >&2; exit 1; }
[[ -f "${ARCHIVE}" ]] || { echo "ERROR: missing backup archive." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker is required." >&2; exit 1; }

work=$(mktemp -d)
trap 'rm -rf "${work}"' EXIT
tar -xzf "${ARCHIVE}" -C "${work}"
bundle=$(find "${work}" -mindepth 1 -maxdepth 1 -type d | head -1)
[[ -n "${bundle}" ]] || { echo "ERROR: archive has no backup bundle." >&2; exit 1; }
(cd "${bundle}" && sha256sum -c manifest.sha256)

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a
project=${COMPOSE_PROJECT_NAME:-smartdiag504}
compose=(docker compose --env-file "${ENV_FILE}" -f compose.yaml)

"${compose[@]}" stop platform-api-a platform-api-b frappe-backend frappe-frontend frappe-websocket frappe-queue-short frappe-queue-long frappe-scheduler garage backup-runner

"${compose[@]}" exec -T postgres dropdb -U "${POSTGRES_USER}" --if-exists "${POSTGRES_DB}"
"${compose[@]}" exec -T postgres createdb -U "${POSTGRES_USER}" "${POSTGRES_DB}"
cat "${bundle}/platform.pgdump" | "${compose[@]}" exec -T postgres pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --no-owner
zstd -dc "${bundle}/erpnext-all.sql.zst" | "${compose[@]}" exec -T mariadb mariadb -uroot -p"${MARIADB_ROOT_PASSWORD}"

docker run --rm --entrypoint bash \
  -v "${project}_frappe-sites:/target" -v "${bundle}:/backup:ro" \
  smartdiag504/backup-runner:0.4.0 -lc 'find /target -mindepth 1 -maxdepth 1 -exec rm -rf {} +; tar --zstd -xf /backup/frappe-sites.tar.zst -C /target'
docker run --rm --entrypoint bash \
  -v "${project}_platform-media:/target" -v "${bundle}:/backup:ro" \
  smartdiag504/backup-runner:0.4.0 -lc 'find /target -mindepth 1 -maxdepth 1 -exec rm -rf {} +; tar --zstd -xf /backup/platform-media.tar.zst -C /target'

for mapping in \
  "garage-config:garage-config.tar.zst" \
  "garage-meta:garage-meta.tar.zst" \
  "garage-data:garage-data.tar.zst"; do
  volume=${mapping%%:*}
  artifact=${mapping#*:}
  docker run --rm --entrypoint bash \
    -v "${project}_${volume}:/target" -v "${bundle}:/backup:ro" \
    smartdiag504/backup-runner:0.4.0 -lc "find /target -mindepth 1 -maxdepth 1 -exec rm -rf {} +; tar --zstd -xf /backup/${artifact} -C /target"
done

"${compose[@]}" up -d garage platform-migrate platform-api-a platform-api-b frappe-backend frappe-frontend frappe-websocket frappe-queue-short frappe-queue-long frappe-scheduler backup-runner
./scripts/wait-ready.sh "${ENV_FILE}" 600
./scripts/smoke-test.sh "${ENV_FILE}"
echo "Restore completed and smoke-tested from ${ARCHIVE}"
