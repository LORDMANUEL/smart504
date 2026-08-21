#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
ENV_FILE=${1:-.env}
[[ -f "${ENV_FILE}" ]] || { echo "ERROR: ${ENV_FILE} does not exist." >&2; exit 1; }
compose=(docker compose --env-file "${ENV_FILE}" -f compose.yaml)

"${compose[@]}" up -d mariadb redis-cache redis-queue
"${compose[@]}" build frappe-configurator
"${compose[@]}" up frappe-configurator
"${compose[@]}" up frappe-site-init
"${compose[@]}" up -d frappe-backend frappe-websocket frappe-frontend frappe-queue-short frappe-queue-long frappe-scheduler

echo "ERPNext/Beveren/SmartDiag site bootstrap completed."
