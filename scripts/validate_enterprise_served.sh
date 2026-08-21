#!/usr/bin/env bash
set -Eeuo pipefail

# Servido contra el dominio real. El token se lee dentro del contenedor y no se imprime.
BASE_URL="${BASE_URL:-https://taller.nexusmedi.org}"
API_CONTAINER="${API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
TOKEN="$(docker exec "$API_CONTAINER" printenv ADMIN_API_TOKEN)"
STAMP="$(date -u +%y%m%d%H%M%S)"
STAFF_PASSWORD="${STAFF_E2E_PASSWORD:-Aceptacion-Productiva-504!}"
OWNER_COOKIE="$(mktemp)"
REVIEWER_COOKIE="$(mktemp)"
APPROVER_COOKIE="$(mktemp)"

cleanup() {
  rm -f "$OWNER_COOKIE" "$REVIEWER_COOKIE" "$APPROVER_COOKIE" "${format_file:-}"
}
trap cleanup EXIT

bootstrap_user() {
  local role="$1" code="$2" email="$3"
  local payload
  payload="$(jq -n \
    --arg email "$email" --arg password "$STAFF_PASSWORD" --arg code "$code" --arg role "$role" \
    '{email:$email,password:$password,employee_code:$code,full_name:("Aceptacion " + $role),role:$role,permissions_json:[],is_active:true,is_superuser:false,is_verified:true}')"
  curl --fail-with-body --silent --show-error \
    -H "X-Admin-Token: $TOKEN" -H 'Content-Type: application/json' \
    --data "$payload" "$BASE_URL/api/v1/staff/users" >/dev/null
}

login() {
  local email="$1" cookie="$2" status
  status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
    -c "$cookie" -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "username=$email" --data-urlencode "password=$STAFF_PASSWORD" \
    "$BASE_URL/api/v1/staff/auth/login")"
  [[ "$status" == "204" ]] || { echo "No se pudo iniciar la sesion productiva de $email" >&2; exit 1; }
}

owner_email="acceptance.owner.$STAMP@nexusmedi.org"
reviewer_email="acceptance.reviewer.$STAMP@nexusmedi.org"
approver_email="acceptance.approver.$STAMP@nexusmedi.org"
bootstrap_user OWNER "OWN-$STAMP" "$owner_email"
bootstrap_user MANAGER "REV-$STAMP" "$reviewer_email"
bootstrap_user ACCOUNTANT "APR-$STAMP" "$approver_email"
login "$owner_email" "$OWNER_COOKIE"
login "$reviewer_email" "$REVIEWER_COOKIE"
login "$approver_email" "$APPROVER_COOKIE"

api() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  if [[ -n "$body" ]]; then
    curl --fail-with-body --silent --show-error \
      -X "$method" -b "$OWNER_COOKIE" -H 'Content-Type: application/json' \
      --data "$body" "$BASE_URL$path"
  else
    curl --fail-with-body --silent --show-error -b "$OWNER_COOKIE" \
      -X "$method" "$BASE_URL$path"
  fi
}

api_as() {
  local cookie="$1" method="$2" path="$3" body="${4:-}"
  curl --fail-with-body --silent --show-error -b "$cookie" \
    -X "$method" -H 'Content-Type: application/json' --data "$body" "$BASE_URL$path"
}

process_erp() {
  api POST /api/v1/operations/integrations/erp/process '{}'
}

supplier="$(api POST /api/v1/operations/enterprise/suppliers "{\"code\":\"E2E-$STAMP\",\"name\":\"Proveedor E2E $STAMP\",\"currency\":\"HNL\",\"payment_terms_days\":30}")"
supplier_id="$(jq -r .id <<<"$supplier")"
process_erp >/dev/null

purchase="$(api POST /api/v1/operations/enterprise/purchase-orders "{\"supplier_id\":\"$supplier_id\",\"currency\":\"HNL\",\"exchange_rate\":1,\"items\":[{\"sku\":\"E2E-FILTRO-$STAMP\",\"description\":\"Filtro de aceite E2E\",\"quantity\":2,\"unit_cost\":175},{\"sku\":\"E2E-PASTILLA-$STAMP\",\"description\":\"Pastilla de freno E2E\",\"quantity\":4,\"unit_cost\":225}],\"notes\":\"Validacion servida SmartDiag504\"}")"
purchase_id="$(jq -r .id <<<"$purchase")"
for status in SUBMITTED APPROVED; do
  purchase="$(api PATCH "/api/v1/operations/enterprise/purchase-orders/$purchase_id/status" "{\"status\":\"$status\"}")"
  process_erp >/dev/null
done
purchase="$(api POST "/api/v1/operations/enterprise/purchase-orders/$purchase_id/receipts" "{\"reference\":\"REC-$STAMP-A\",\"note\":\"Recepcion parcial E2E\",\"items\":[{\"sku\":\"E2E-FILTRO-$STAMP\",\"quantity\":1},{\"sku\":\"E2E-PASTILLA-$STAMP\",\"quantity\":2}]}")"
[[ "$(jq -r .status <<<"$purchase")" == "PARTIALLY_RECEIVED" ]]
process_erp >/dev/null
purchase="$(api POST "/api/v1/operations/enterprise/purchase-orders/$purchase_id/receipts" "{\"reference\":\"REC-$STAMP-B\",\"note\":\"Recepcion final E2E\",\"items\":[{\"sku\":\"E2E-FILTRO-$STAMP\",\"quantity\":1},{\"sku\":\"E2E-PASTILLA-$STAMP\",\"quantity\":2}]}")"
[[ "$(jq -r .status <<<"$purchase")" == "RECEIVED" ]]
process_erp >/dev/null

import_case="$(api POST /api/v1/operations/enterprise/import-cases "{\"purchase_order_id\":\"$purchase_id\",\"incoterm\":\"CIF\",\"origin_country\":\"US\",\"destination_port\":\"Puerto Cortes\",\"allocation_method\":\"BY_VALUE\",\"costs\":[{\"kind\":\"FREIGHT\",\"description\":\"Flete E2E\",\"amount\":250,\"currency\":\"HNL\"}]}")"
import_id="$(jq -r .id <<<"$import_case")"
import_case="$(api PATCH "/api/v1/operations/enterprise/import-cases/$import_id" "{\"costs\":[{\"kind\":\"FREIGHT\",\"description\":\"Flete E2E\",\"amount\":250,\"currency\":\"HNL\"},{\"kind\":\"CUSTOMS\",\"description\":\"Aduana E2E\",\"amount\":85,\"currency\":\"HNL\"}],\"documents\":[{\"kind\":\"BILL_OF_LADING\",\"name\":\"BL E2E\",\"url\":\"https://example.test/bl.pdf\"}]}")"
for status in IN_TRANSIT CUSTOMS RECEIVED ALLOCATED; do
  import_case="$(api PATCH "/api/v1/operations/enterprise/import-cases/$import_id/status" "{\"status\":\"$status\"}")"
done
process_erp >/dev/null

contract="$(api POST /api/v1/operations/enterprise/hr/contracts "{\"employee_code\":\"E2E-$STAMP\",\"employee_name\":\"Tecnico E2E $STAMP\",\"date_of_birth\":\"1990-01-15\",\"job_title\":\"Tecnico especialista\",\"contract_type\":\"PERMANENT\",\"start_date\":\"2026-08-01\",\"monthly_salary\":18000,\"standard_hours_weekly\":44,\"currency\":\"HNL\",\"schedule\":{\"weekdays\":\"LUN-VIE\",\"start\":\"08:00\",\"end\":\"17:00\"}}")"
contract_id="$(jq -r .id <<<"$contract")"
process_erp >/dev/null
attendance="$(api POST /api/v1/operations/enterprise/hr/attendance "{\"contract_id\":\"$contract_id\",\"work_date\":\"2026-08-17\",\"regular_hours\":8,\"overtime_hours\":1}")"
attendance_id="$(jq -r .id <<<"$attendance")"
attendance="$(api PATCH "/api/v1/operations/enterprise/hr/attendance/$attendance_id/overtime" '{"status":"APPROVED","note":"Horas E2E verificadas por RRHH"}')"
[[ "$(jq -r .overtime_status <<<"$attendance")" == "APPROVED" ]]
contract="$(api PATCH "/api/v1/operations/enterprise/hr/contracts/$contract_id" '{"job_title":"Tecnico senior","monthly_salary":19000,"schedule":{"weekdays":"LUN-VIE","start":"07:30","end":"16:30"}}')"
payroll="$(api POST /api/v1/operations/enterprise/hr/payroll-runs "{\"period_start\":\"2026-08-01\",\"period_end\":\"2026-08-31\",\"contract_ids\":[\"$contract_id\"],\"adjustments\":[{\"contract_id\":\"$contract_id\",\"kind\":\"COMMISSION\",\"description\":\"Comision E2E\",\"amount\":500}]}")"
payroll_id="$(jq -r .id <<<"$payroll")"
payroll="$(api_as "$REVIEWER_COOKIE" PATCH "/api/v1/operations/enterprise/hr/payroll-runs/$payroll_id/status" '{"status":"REVIEWED"}')"
payroll="$(api_as "$APPROVER_COOKIE" PATCH "/api/v1/operations/enterprise/hr/payroll-runs/$payroll_id/status" '{"status":"APPROVED"}')"
process_erp >/dev/null

vin="HNE2E${STAMP}VIN"
used="$(api POST /api/v1/operations/enterprise/used-vehicles "{\"vin\":\"$vin\",\"make\":\"Honda\",\"model\":\"Civic\",\"model_year\":2008,\"mileage_km\":165000,\"acquisition_type\":\"CONSIGNMENT\",\"acquisition_cost\":120000,\"target_sale_price\":145000,\"owner_name\":\"Propietario E2E\"}")"
used_id="$(jq -r .id <<<"$used")"
used="$(api PATCH "/api/v1/operations/enterprise/used-vehicles/$used_id/status" '{"status":"ACQUIRED"}')"
process_erp >/dev/null

channel="$(api POST /api/v1/operations/enterprise/social/channels "{\"channel_type\":\"WHATSAPP\",\"name\":\"WhatsApp E2E $STAMP\",\"external_account_id\":\"wa-$STAMP\",\"credential_reference\":\"secret://whatsapp/e2e-$STAMP\"}")"
channel_id="$(jq -r .id <<<"$channel")"
conversation="$(api POST /api/v1/operations/enterprise/social/conversations "{\"channel_id\":\"$channel_id\",\"contact_name\":\"Cliente E2E\",\"contact_handle\":\"+50499990000\",\"consent_status\":\"OPTED_IN\",\"subject\":\"Consulta E2E\"}")"
conversation_id="$(jq -r .id <<<"$conversation")"
message="$(api POST "/api/v1/operations/enterprise/social/conversations/$conversation_id/messages" '{"direction":"OUTBOUND","body":"Respuesta E2E aprobada por una persona.","human_approved":true}')"

format_file="$(mktemp --suffix=.html)"
printf '%s' '<h1>{{ company.name }}</h1><p>{{ document.number }}</p>' > "$format_file"
template="$(curl --fail-with-body --silent --show-error -b "$OWNER_COOKIE" -F "code=E2E_INVOICE_$STAMP" -F 'name=Factura E2E cargada' -F 'document_type=INVOICE' -F 'paper_size=LETTER' -F 'change_note=Carga E2E' -F "html_file=@$format_file;type=text/html" "$BASE_URL/api/v1/operations/documents/templates/import")"
template_id="$(jq -r .id <<<"$template")"
template_export_status="$(curl --silent --output /dev/null --write-out '%{http_code}' -b "$OWNER_COOKIE" "$BASE_URL/api/v1/operations/documents/templates/$template_id/export")"
[[ "$template_export_status" == "200" ]]

overview="$(api GET /api/v1/operations/enterprise/overview)"
jq -n \
  --arg supplier "$(jq -r --arg id "$supplier_id" '.suppliers[] | select(.id == $id) | .erp_sync_status' <<<"$overview")" \
  --arg purchase "$(jq -r --arg id "$purchase_id" '.purchase_orders[] | select(.id == $id) | .status + ":" + .erp_sync_status' <<<"$overview")" \
  --arg import "$(jq -r --arg id "$import_id" '.import_cases[] | select(.id == $id) | .status + ":" + .landed_cost_status' <<<"$overview")" \
  --arg contract "$(jq -r --arg id "$contract_id" '.contracts[] | select(.id == $id) | .erp_sync_status' <<<"$overview")" \
  --arg payroll "$(jq -r --arg id "$payroll_id" '.payroll_runs[] | select(.id == $id) | .status + ":" + .erp_sync_status' <<<"$overview")" \
  --arg used "$(jq -r --arg id "$used_id" '.used_vehicles[] | select(.id == $id) | .status' <<<"$overview")" \
  --arg social "$(jq -r '.status' <<<"$message")" \
  --arg overtime "$(jq -r '.overtime_status' <<<"$attendance")" \
  --arg template "$(jq -r '.code + ":v" + (.current_version|tostring)' <<<"$template")" \
  --argjson counts "$(jq '.counts' <<<"$overview")" \
  '{supplier:$supplier,purchase:$purchase,import:$import,contract:$contract,payroll:$payroll,overtime:$overtime,template:$template,used_vehicle:$used,social_message:$social,counts:$counts}'
