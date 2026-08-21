#!/usr/bin/env bash
set -Eeuo pipefail

: "${ERP_SITE_NAME:?ERP_SITE_NAME is required}"
: "${MARIADB_ROOT_PASSWORD:?MARIADB_ROOT_PASSWORD is required}"
: "${ERP_ADMIN_PASSWORD:?ERP_ADMIN_PASSWORD is required}"

DB_HOST=${DB_HOST:-mariadb}
DB_PORT=${DB_PORT:-3306}
ERP_EXTERNAL_URL=${ERP_EXTERNAL_URL:-http://erp.localhost}

cd /home/frappe/frappe-bench
until python - <<'PY'
import os
import socket

with socket.create_connection((os.environ.get("DB_HOST", "mariadb"), int(os.environ.get("DB_PORT", "3306"))), 3):
    pass
PY
do
  echo "Waiting for MariaDB at ${DB_HOST}:${DB_PORT}..."
  sleep 3
done

if [[ ! -f "sites/${ERP_SITE_NAME}/site_config.json" ]]; then
  bench new-site "${ERP_SITE_NAME}" \
    --db-type mariadb \
    --db-host "${DB_HOST}" \
    --db-port "${DB_PORT}" \
    --db-root-username root \
    --db-root-password "${MARIADB_ROOT_PASSWORD}" \
    --admin-password "${ERP_ADMIN_PASSWORD}" \
    --mariadb-user-host-login-scope='%' \
    --no-mariadb-socket
fi

installed_apps=$(bench --site "${ERP_SITE_NAME}" list-apps 2>/dev/null || true)
for app in erpnext beveren_fsm smartdiag_workshop; do
  if ! grep -qx "${app}" <<<"${installed_apps}"; then
    bench --site "${ERP_SITE_NAME}" install-app "${app}"
    installed_apps+=$'\n'"${app}"
  fi
done

bench --site "${ERP_SITE_NAME}" migrate

if [[ -n "${FRAPPE_API_KEY:-}" && -n "${FRAPPE_API_SECRET:-}" ]]; then
  integration_kwargs=$(python - <<'PY'
import json
import os
print(json.dumps({"api_key": os.environ["FRAPPE_API_KEY"], "api_secret": os.environ["FRAPPE_API_SECRET"]}))
PY
)
  bench --site "${ERP_SITE_NAME}" execute \
    smartdiag_workshop.setup.integration.ensure_integration_user \
    --kwargs "${integration_kwargs}"
fi

bench --site "${ERP_SITE_NAME}" set-config host_name "${ERP_EXTERNAL_URL}"
bench --site "${ERP_SITE_NAME}" set-config developer_mode 0
bench --site "${ERP_SITE_NAME}" enable-scheduler
bench --site "${ERP_SITE_NAME}" clear-cache
printf '%s\n' "${ERP_SITE_NAME}" > sites/currentsite.txt

echo "ERPNext site ${ERP_SITE_NAME} initialized with ERPNext, Beveren FSM and SmartDiag Workshop."
