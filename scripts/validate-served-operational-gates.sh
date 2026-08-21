#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${BASE_URL:-https://taller.nexusmedi.org}"
api_container="${API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
token="$(docker exec "$api_container" printenv ADMIN_API_TOKEN)"
stamp="$(date -u +%y%m%d%H%M%S)"

api() {
  local method="$1" path="$2" body="${3:-}"
  local response http_code
  response="$(mktemp)"
  local args=(--silent --show-error --output "$response" --write-out '%{http_code}' -X "$method" -H "X-Admin-Token: $token")
  if [[ -n "$body" ]]; then
    args+=(-H 'Content-Type: application/json' --data "$body")
  fi
  http_code="$(curl "${args[@]}" "$base_url$path")"
  if (( http_code >= 400 )); then
    printf 'HTTP %s en %s %s: ' "$http_code" "$method" "$path" >&2
    cat "$response" >&2
    rm -f "$response"
    return 1
  fi
  cat "$response"
  rm -f "$response"
}

customer="$(api POST /api/v1/operations/customers "{\"full_name\":\"Cliente control $stamp\",\"phone\":\"+50499995040\",\"email\":\"control+$stamp@nexusmedi.org\"}")"
customer_id="$(jq -er .id <<<"$customer")"
vehicle="$(api POST /api/v1/operations/vehicles "{\"customer_id\":\"$customer_id\",\"vin\":\"SDA50$stamp\",\"plate\":\"T${stamp:6:6}\",\"make\":\"Honda\",\"model\":\"Civic\",\"model_year\":2008,\"mileage_km\":86040}")"
vehicle_id="$(jq -er .id <<<"$vehicle")"
order="$(api POST /api/v1/operations/work-orders "{\"customer_id\":\"$customer_id\",\"vehicle_id\":\"$vehicle_id\",\"title\":\"Control servido 360\",\"concern\":\"Validar ingreso, tiempo y calidad\",\"assigned_technicians\":[\"TECNICO-E2E\"],\"bay_code\":\"BAHIA-E2E\",\"actor\":\"recepcion-e2e\"}")"
order_id="$(jq -er .id <<<"$order")"

api POST "/api/v1/operations/work-orders/$order_id/check-in" '{"mileage_km":86040,"fuel_percent":55,"accessories":["Llave","Llanta de repuesto"],"exterior_notes":"Rayon previo documentado","customer_name":"Cliente control","customer_accepted":true,"actor":"recepcion-e2e"}' >/dev/null
api POST "/api/v1/operations/work-orders/$order_id/timer" '{"action":"START","note":"Diagnostico servido","actor":"tecnico-e2e"}' >/dev/null
api POST "/api/v1/operations/work-orders/$order_id/timer" '{"action":"STOP","note":"Trabajo finalizado","actor":"tecnico-e2e"}' >/dev/null
api POST "/api/v1/operations/work-orders/$order_id/quality" '{"checklist":{"frenos":true,"niveles":true,"limpieza":true},"road_test_required":true,"road_test_result":"PASS","notes":"Sin novedad","result":"PASS","actor":"supervisor-calidad-e2e"}' >/dev/null
api POST "/api/v1/operations/work-orders/$order_id/transitions" "{\"to_status\":\"QUOTED_BY_TECHNICIAN\",\"reason\":\"cotizacion preparada\",\"actor\":\"asesor-e2e\",\"idempotency_key\":\"$stamp-quoted\"}" >/dev/null
api POST "/api/v1/operations/work-orders/$order_id/transitions" "{\"to_status\":\"PENDING_CUSTOMER_APPROVAL\",\"reason\":\"enviada al cliente\",\"actor\":\"asesor-e2e\",\"idempotency_key\":\"$stamp-approval\"}" >/dev/null
ready="$(api POST "/api/v1/operations/work-orders/$order_id/transitions" "{\"to_status\":\"READY_TO_INVOICE\",\"reason\":\"controles completos\",\"actor\":\"caja-e2e\",\"idempotency_key\":\"$stamp-ready\"}")"

jq -n \
  --arg order_id "$order_id" \
  --arg number "$(jq -er .number <<<"$ready")" \
  --arg status "$(jq -er .status <<<"$ready")" \
  --arg erp "$(jq -er .erp_sync_status <<<"$ready")" \
  '{status:"PASS",work_order_id:$order_id,number:$number,operational_status:$status,erp_sync_status:$erp,controls:["CHECK_IN_360","TIMER_STOPPED","QUALITY_PASS"]}'
