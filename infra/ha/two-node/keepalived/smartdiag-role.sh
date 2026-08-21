#!/usr/bin/env bash
set -euo pipefail
ROLE=${1:?role required}
ROOT=${SMARTDIAG_ROOT:-/opt/smartdiag504}
ENV_FILE=${SMARTDIAG_ENV_FILE:-$ROOT/.env}
LOG=/var/log/smartdiag-ha-role.log
cd "$ROOT"
case "$ROLE" in
  master)
    docker compose --env-file "$ENV_FILE" up -d frappe-backend frappe-frontend frappe-websocket frappe-queue-short frappe-queue-long frappe-scheduler
    ;;
  backup|fault)
    docker compose --env-file "$ENV_FILE" stop frappe-scheduler frappe-queue-short frappe-queue-long frappe-websocket frappe-frontend frappe-backend || true
    ;;
  *) exit 2 ;;
esac
printf '%s role=%s host=%s\n' "$(date -u +%FT%TZ)" "$ROLE" "$(hostname)" >> "$LOG"
