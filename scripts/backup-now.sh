#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${ROOT_DIR}/scripts/backup.sh" --env-file "${1:-.env}" --output "${2:-${ROOT_DIR}/backups}"
