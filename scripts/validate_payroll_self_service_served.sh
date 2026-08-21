#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${BASE_URL:-https://taller.nexusmedi.org}"
API_CONTAINER="${API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
TOKEN="$(docker exec "$API_CONTAINER" printenv ADMIN_API_TOKEN)"
STAMP="$(date -u +%y%m%d%H%M%S)"
EMAIL="tecnico.nomina.$STAMP@example.com"
PASSWORD="Temporal-504-$STAMP!"
COOKIE="$(mktemp)"
PREPARER_COOKIE="$(mktemp)"
REVIEWER_COOKIE="$(mktemp)"
APPROVER_COOKIE="$(mktemp)"
HTML="$(mktemp --suffix=.html)"
trap 'rm -f "$COOKIE" "$PREPARER_COOKIE" "$REVIEWER_COOKIE" "$APPROVER_COOKIE" "$HTML"' EXIT

bootstrap_user() {
  local role="$1" code="$2" email="$3" payload
  payload="$(jq -n --arg email "$email" --arg password "$PASSWORD" --arg code "$code" --arg role "$role" \
    '{email:$email,password:$password,employee_code:$code,full_name:("Aceptacion " + $role),role:$role,permissions_json:[],is_active:true,is_superuser:false,is_verified:true}')"
  curl --fail-with-body --silent --show-error -H "X-Admin-Token: $TOKEN" \
    -H 'Content-Type: application/json' --data "$payload" "$BASE_URL/api/v1/staff/users" >/dev/null
}

login_staff() {
  local email="$1" cookie="$2" status
  status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' -c "$cookie" \
    -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=$email" --data-urlencode "password=$PASSWORD" \
    "$BASE_URL/api/v1/staff/auth/login")"
  [[ "$status" == "204" ]] || { echo "No se pudo iniciar sesion: $email" >&2; exit 1; }
}

preparer_email="nomina.prepara.$STAMP@example.com"
reviewer_email="nomina.revisa.$STAMP@example.com"
approver_email="nomina.aprueba.$STAMP@example.com"
bootstrap_user OWNER "NPR-$STAMP" "$preparer_email"
bootstrap_user MANAGER "NRV-$STAMP" "$reviewer_email"
bootstrap_user ACCOUNTANT "NAP-$STAMP" "$approver_email"
login_staff "$preparer_email" "$PREPARER_COOKIE"
login_staff "$reviewer_email" "$REVIEWER_COOKIE"
login_staff "$approver_email" "$APPROVER_COOKIE"

admin_api() {
  local method="$1" path="$2" body="${3:-}"
  local response
  if [[ -n "$body" ]]; then
    if ! response="$(curl --fail-with-body --silent --show-error -b "$PREPARER_COOKIE" -X "$method" \
      -H 'Content-Type: application/json' --data "$body" "$BASE_URL$path")"; then
      printf '%s\n' "$response" >&2
      return 1
    fi
  else
    if ! response="$(curl --fail-with-body --silent --show-error -b "$PREPARER_COOKIE" -X "$method" "$BASE_URL$path")"; then
      printf '%s\n' "$response" >&2
      return 1
    fi
  fi
  printf '%s' "$response"
}

staff_api() {
  local cookie="$1" method="$2" path="$3" body="${4:-}"
  curl --fail-with-body --silent --show-error -b "$cookie" -X "$method" \
    -H 'Content-Type: application/json' --data "$body" "$BASE_URL$path"
}

employee_api() {
  local method="$1" path="$2" body="${3:-}"
  if [[ -n "$body" ]]; then
    curl --fail-with-body --silent --show-error -b "$COOKIE" -c "$COOKIE" -X "$method" \
      -H 'Content-Type: application/json' --data "$body" "$BASE_URL$path"
  else
    curl --fail-with-body --silent --show-error -b "$COOKIE" -c "$COOKIE" -X "$method" "$BASE_URL$path"
  fi
}

user="$(admin_api POST /api/v1/staff/users "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"Tecnico Nomina $STAMP\",\"job_title\":\"Tecnico\",\"role\":\"TECHNICIAN\",\"permissions_json\":[],\"is_active\":true,\"is_verified\":true}")"
employee_code="$(jq -er .employee_code <<<"$user")"
[[ "$employee_code" == EMP-* ]]

contract="$(admin_api POST /api/v1/operations/enterprise/hr/contracts "{\"employee_name\":\"Tecnico Nomina $STAMP\",\"email\":\"$EMAIL\",\"date_of_birth\":\"1994-04-12\",\"national_id\":\"0801-$STAMP\",\"address\":\"Tegucigalpa, Honduras\",\"job_title\":\"Tecnico\",\"contract_type\":\"PERMANENT\",\"start_date\":\"2026-01-01\",\"monthly_salary\":18000,\"payment_type\":\"MONTHLY\",\"base_pay_amount\":18000,\"standard_hours_weekly\":44,\"currency\":\"HNL\"}")"
contract_id="$(jq -er .id <<<"$contract")"
[[ "$(jq -r .employee_code <<<"$contract")" == "$employee_code" ]]

payroll="$(admin_api POST /api/v1/operations/enterprise/hr/payroll-runs "{\"period_start\":\"2026-08-01\",\"period_end\":\"2026-08-31\",\"contract_ids\":[\"$contract_id\"]}")"
payroll_id="$(jq -er .id <<<"$payroll")"
payroll="$(staff_api "$REVIEWER_COOKIE" PATCH "/api/v1/operations/enterprise/hr/payroll-runs/$payroll_id/status" '{"status":"REVIEWED"}')"
payroll="$(staff_api "$APPROVER_COOKIE" PATCH "/api/v1/operations/enterprise/hr/payroll-runs/$payroll_id/status" '{"status":"APPROVED"}')"
for _ in 1 2 3; do admin_api POST /api/v1/operations/integrations/erp/process '{}' >/dev/null; done
enterprise_overview="$(admin_api GET /api/v1/operations/enterprise/overview)"
payroll="$(jq -cer --arg id "$payroll_id" '.payroll_runs[] | select(.id == $id)' <<<"$enterprise_overview")"

login_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' -c "$COOKIE" \
  -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=$EMAIL" --data-urlencode "password=$PASSWORD" "$BASE_URL/api/v1/staff/auth/login")"
[[ "$login_status" == "204" ]]
overview="$(employee_api GET /api/v1/staff/self-service/overview)"
voucher_id="$(jq -er '.vouchers[0].id' <<<"$overview")"
[[ "$(jq -r .contract.employee_code <<<"$overview")" == "$employee_code" ]]

employee_api GET "/api/v1/staff/self-service/vouchers/$voucher_id/html" > "$HTML"
grep -q 'Imprimir o guardar PDF' "$HTML"
employee_api POST /api/v1/staff/self-service/punch '{"action":"CHECK_IN","note":"Prueba servida"}' >/dev/null
attendance="$(employee_api POST /api/v1/staff/self-service/punch '{"action":"CHECK_OUT","note":"Prueba servida"}')"
leave_date="$(date -u -d '+5 days' +%F)"
leave="$(employee_api POST /api/v1/staff/self-service/leave-requests "{\"leave_type\":\"PERSONAL\",\"start_date\":\"$leave_date\",\"end_date\":\"$leave_date\",\"reason\":\"Prueba funcional servida\"}")"

jq -n \
  --arg employee_code "$employee_code" \
  --arg contract_link "$(jq -r .contract.employee_code <<<"$overview")" \
  --arg payroll "$(jq -r '.status + ":" + .erp_sync_status' <<<"$payroll")" \
  --arg voucher "HTML_PRINT_OK" \
  --arg attendance "$(jq -r '.status + ":" + (.regular_hours|tostring)' <<<"$attendance")" \
  --arg leave "$(jq -r .status <<<"$leave")" \
  '{employee_code:$employee_code,contract_link:$contract_link,payroll:$payroll,voucher:$voucher,attendance:$attendance,leave:$leave}'
