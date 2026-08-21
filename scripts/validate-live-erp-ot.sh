#!/usr/bin/env bash
set -Eeuo pipefail

api_container="${SMARTDIAG_API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
api_base="${SMARTDIAG_API_BASE:-https://taller.nexusmedi.org/api/v1/operations}"
admin_token="$(docker exec "$api_container" printenv ADMIN_API_TOKEN)"
run_id="$(date -u +%Y%m%dT%H%M%SZ)"

request() {
  local method="$1"
  local path="$2"
  local payload="${3:-}"
  if [[ -n "$payload" ]]; then
    curl --fail-with-body --silent --show-error \
      -X "$method" -H "X-Admin-Token: $admin_token" \
      -H "Content-Type: application/json" --data "$payload" \
      "$api_base$path"
  else
    curl --fail-with-body --silent --show-error \
      -X "$method" -H "X-Admin-Token: $admin_token" \
      "$api_base$path"
  fi
}

customer="$(request POST /customers "{\"full_name\":\"Cliente auditoria ERP $run_id\",\"phone\":\"+50499990000\",\"email\":\"audit+$run_id@nexusmedi.org\"}")"
customer_id="$(jq -er .id <<<"$customer")"

vin="SD5${run_id:2:14}"
vehicle="$(request POST /vehicles "{\"customer_id\":\"$customer_id\",\"vin\":\"$vin\",\"plate\":\"E2E504\",\"make\":\"Ford\",\"model\":\"Escape\",\"model_year\":2020,\"mileage_km\":50400}")"
vehicle_id="$(jq -er .id <<<"$vehicle")"

work_order="$(request POST /work-orders "{\"customer_id\":\"$customer_id\",\"vehicle_id\":\"$vehicle_id\",\"title\":\"Auditoria de convergencia ERP\",\"concern\":\"Validar escritura autoritativa y reconciliacion\",\"assigned_technicians\":[\"TECNICO-E2E\"],\"bay_code\":\"BAHIA-E2E\",\"actor\":\"AUDITOR-E2E\"}")"
work_order_id="$(jq -er .id <<<"$work_order")"
work_order_number="$(jq -er .number <<<"$work_order")"
erp_reference="$(jq -er .erpnext_service_order_id <<<"$work_order")"
[[ "$(jq -er .erp_sync_status <<<"$work_order")" == "SYNCED" ]]

updated="$(request PATCH "/work-orders/$work_order_id" '{"diagnosis":"Diagnostico confirmado en recorrido servido","bay_code":"BAHIA-QC"}')"
[[ "$(jq -er .erp_sync_status <<<"$updated")" == "SYNCED" ]]
[[ "$(jq -er .diagnosis <<<"$updated")" == "Diagnostico confirmado en recorrido servido" ]]

reconciled="$(request POST "/work-orders/$work_order_id/reconcile")"
[[ "$(jq -er .erp_sync_status <<<"$reconciled")" == "SYNCED" ]]
[[ "$(jq -er .erpnext_service_order_id <<<"$reconciled")" == "$erp_reference" ]]
[[ "$(jq -er .diagnosis <<<"$reconciled")" == "Diagnostico confirmado en recorrido servido" ]]

jq -n \
  --arg run_id "$run_id" \
  --arg work_order_id "$work_order_id" \
  --arg work_order_number "$work_order_number" \
  --arg erp_service_order "$erp_reference" \
  --arg sync_status "$(jq -er .erp_sync_status <<<"$reconciled")" \
  '{status:"PASS",run_id:$run_id,work_order_id:$work_order_id,work_order_number:$work_order_number,erp_service_order:$erp_service_order,sync_status:$sync_status}'
