#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
ENV_FILE=${ENV_FILE:-.env}
OUTPUT_DIR=${BACKUP_DIR:-./backups}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --output) OUTPUT_DIR="$2"; shift 2 ;;
    -h|--help) echo "Usage: $0 [--env-file FILE] [--output DIRECTORY]"; exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; exit 2 ;;
  esac
done

[[ -f "${ENV_FILE}" ]] || { echo "ERROR: missing ${ENV_FILE}." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker is required." >&2; exit 1; }
mkdir -p "${OUTPUT_DIR}"
chmod 700 "${OUTPUT_DIR}"
compose=(docker compose --env-file "${ENV_FILE}" -f compose.yaml)
"${compose[@]}" run --rm -e RUN_ONCE=1 backup-runner
stamp=$("${compose[@]}" run --rm --no-deps --entrypoint bash backup-runner -lc 'cat /backups/LAST_SUCCESS')
archive="${OUTPUT_DIR}/smartdiag504-${stamp}.tar.gz"
"${compose[@]}" run --rm --no-deps --entrypoint bash \
  -v "$(cd "${OUTPUT_DIR}" && pwd):/export" \
  backup-runner -lc "tar -C /backups -czf /export/$(basename "${archive}") ${stamp} LAST_SUCCESS"
sha256sum "${archive}" > "${archive}.sha256"
./scripts/verify-backup.sh "${archive}"
echo "Backup exported: ${archive}"
