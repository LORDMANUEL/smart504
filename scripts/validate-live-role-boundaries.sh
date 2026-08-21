#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${BASE_URL:-https://taller.nexusmedi.org}"
api_container="${SMARTDIAG_API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
admin_token="$(docker exec "$api_container" printenv ADMIN_API_TOKEN)"
staff_password="${STAFF_E2E_PASSWORD:-Rol-E2E-Seguro-504!}"
stamp="$(date -u +%y%m%d%H%M%S)"
cookie_file="$(mktemp)"
trap 'rm -f "$cookie_file"' EXIT

create_role() {
  local role="$1" code="$2" email="$3" branch_id="${4:-}"
  local payload
  payload="$(jq -n \
    --arg email "$email" --arg password "$staff_password" --arg code "$code" \
    --arg role "$role" --arg branch "$branch_id" \
    '{email:$email,password:$password,employee_code:$code,full_name:("Validacion " + $role),role:$role,permissions_json:[],is_active:true,is_superuser:false,is_verified:true} + (if $branch == "" then {} else {branch_id:$branch} end)')"
  curl --fail-with-body --silent --show-error \
    -H "X-Admin-Token: $admin_token" -H 'Content-Type: application/json' \
    --data "$payload" \
    "$base_url/api/v1/staff/users" >/dev/null
}

login() {
  local email="$1"
  : >"$cookie_file"
  local status
  status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
    -c "$cookie_file" -X POST \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=$email" \
    --data-urlencode "password=$staff_password" \
    "$base_url/api/v1/staff/auth/login")"
  [[ "$status" == "204" ]] || { echo "LOGIN_FAIL $email $status" >&2; exit 1; }
}

status_for() {
  local method="$1" path="$2"
  curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
    -b "$cookie_file" -X "$method" -H 'Content-Type: application/json' \
    --data '{}' "$base_url$path"
}

marketing_email="security.marketing.$stamp@nexusmedi.org"
technician_email="security.technician.$stamp@nexusmedi.org"
accountant_email="security.accountant.$stamp@nexusmedi.org"
cashier_email="security.cashier.$stamp@nexusmedi.org"
overview="$(curl --fail-with-body --silent --show-error -H "X-Admin-Token: $admin_token" \
  "$base_url/api/v1/operations/control/overview")"
main_branch_id="$(jq -er '.branches[] | select(.code == "MAIN") | .id' <<<"$overview")"
isolation_branch_id="$(curl --fail-with-body --silent --show-error \
  -H "X-Admin-Token: $admin_token" -H 'Content-Type: application/json' \
  --data "{\"code\":\"SEC-$stamp\",\"name\":\"Sucursal aislamiento $stamp\"}" \
  "$base_url/api/v1/operations/control/branches" | jq -er '.id')"
create_role MARKETING "MKT-$stamp" "$marketing_email" "$main_branch_id"
create_role TECHNICIAN "TEC-$stamp" "$technician_email" "$isolation_branch_id"
create_role ACCOUNTANT "CON-$stamp" "$accountant_email" "$main_branch_id"
create_role CASHIER "CAJ-$stamp" "$cashier_email" "$main_branch_id"

login "$marketing_email"
marketing="$(curl --fail-with-body --silent --show-error -b "$cookie_file" \
  "$base_url/api/v1/operations/enterprise/overview")"
[[ "$(jq '.suppliers | length' <<<"$marketing")" == "0" ]]
[[ "$(jq '.contracts | length' <<<"$marketing")" == "0" ]]

login "$technician_email"
technician_work_orders="$(curl --fail-with-body --silent --show-error -b "$cookie_file" \
  "$base_url/api/v1/operations/work-orders")"
[[ "$(jq 'length' <<<"$technician_work_orders")" == "0" ]]
technician_documents_read="$(status_for GET /api/v1/operations/documents/templates)"
technician_documents_write="$(status_for POST /api/v1/operations/documents/templates)"
technician_catalog_write="$(status_for POST /api/v1/admin/catalog/products)"
[[ "$technician_documents_read" == "200" ]]
[[ "$technician_documents_write" == "403" ]]
[[ "$technician_catalog_write" == "403" ]]

login "$accountant_email"
accountant="$(curl --fail-with-body --silent --show-error -b "$cookie_file" \
  "$base_url/api/v1/operations/enterprise/overview")"
[[ "$(jq '.social_channels | length' <<<"$accountant")" == "0" ]]
[[ "$(jq '.social_conversations | length' <<<"$accountant")" == "0" ]]

login "$cashier_email"
work_order_id="$(curl --fail-with-body --silent --show-error -b "$cookie_file" \
  "$base_url/api/v1/operations/work-orders" | jq -er '.[0].id')"
cashier_ot_write="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  -b "$cookie_file" -X PATCH -H 'Content-Type: application/json' \
  --data '{"diagnosis":"Caja no debe modificar diagnosticos"}' \
  "$base_url/api/v1/operations/work-orders/$work_order_id")"
[[ "$cashier_ot_write" == "403" ]]

jq -n '{status:"PASS",branch_isolation:true,marketing_hr_hidden:true,technician_document_write:403,technician_catalog_write:403,accountant_social_hidden:true,cashier_work_order_write:403}'
