#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${BASE_URL:-https://taller.nexusmedi.org}"
: "${STAFF_DEMO_PASSWORD:?STAFF_DEMO_PASSWORD es obligatorio}"
: "${CLIENT_DEMO_PASSWORD:?CLIENT_DEMO_PASSWORD es obligatorio}"

staff_users=(
  demo.admin@smartdiag504.com
  recepcion.demo@taller.nexusmedi.org
  tecnico.demo@taller.nexusmedi.org
  caja.demo@taller.nexusmedi.org
  bodega.demo@taller.nexusmedi.org
  gerencia.demo@taller.nexusmedi.org
  mercadeo.demo@taller.nexusmedi.org
  auditor.demo@taller.nexusmedi.org
  contador.demo@taller.nexusmedi.org
)

for user in "${staff_users[@]}"; do
  status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
    -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=${user}" --data-urlencode "password=${STAFF_DEMO_PASSWORD}" \
    "${base_url}/api/v1/staff/auth/login")"
  printf '%s %s\n' "$user" "$status"
  [[ "$status" == "204" ]]
done

client_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=cliente.demo@smartdiag504.com" \
  --data-urlencode "password=${CLIENT_DEMO_PASSWORD}" \
  "${base_url}/api/v1/client-auth/login")"
printf '%s %s\n' cliente.demo@smartdiag504.com "$client_status"
[[ "$client_status" == "204" ]]
