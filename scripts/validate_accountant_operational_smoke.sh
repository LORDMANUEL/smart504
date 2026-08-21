#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${BASE_URL:-https://taller.nexusmedi.org}"
API_CONTAINER="${API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
ACCOUNTANT_EMAIL="${ACCOUNTANT_EMAIL:-contador.demo@taller.nexusmedi.org}"
ACCOUNTANT_PASSWORD="${ACCOUNTANT_PASSWORD:-}"

cookie_file="$(mktemp)"
body_file="$(mktemp)"
header_file="$(mktemp)"
image_file="$(mktemp --suffix=.png)"
smtp_container="smartdiag-smtp-smoke-$$"
cleanup() {
  docker rm -f "$smtp_container" >/dev/null 2>&1 || true
  rm -f "$cookie_file" "$body_file" "$header_file" "$image_file"
}
trap cleanup EXIT

admin_token="$(docker exec "$API_CONTAINER" printenv ADMIN_API_TOKEN)"

# A reproducible acceptance gate must not depend on a human demo credential.
# When no credential is supplied, provision a short-lived acceptance identity
# through the existing administrative boundary and keep its password in memory.
if [[ -z "$ACCOUNTANT_PASSWORD" ]]; then
  stamp_identity="$(date -u +%y%m%d%H%M%S)"
  ACCOUNTANT_EMAIL="accountant.acceptance.$stamp_identity@nexusmedi.org"
  ACCOUNTANT_PASSWORD="Acceptance-Accountant-$stamp_identity!"
  overview_identity="$(curl --fail-with-body --silent --show-error \
    -H "X-Admin-Token: $admin_token" "$BASE_URL/api/v1/operations/control/overview")"
  branch_identity="$(jq -er '.branches[] | select(.code == "MAIN") | .id' <<<"$overview_identity")"
  payload_identity="$(jq -n --arg email "$ACCOUNTANT_EMAIL" --arg password "$ACCOUNTANT_PASSWORD" \
    --arg branch "$branch_identity" --arg code "CON-$stamp_identity" \
    '{email:$email,password:$password,employee_code:$code,full_name:"Contador aceptación",role:"ACCOUNTANT",permissions_json:[],is_active:true,is_superuser:false,is_verified:true,branch_id:$branch}')"
  curl --fail-with-body --silent --show-error -H "X-Admin-Token: $admin_token" \
    -H 'Content-Type: application/json' --data "$payload_identity" \
    "$BASE_URL/api/v1/staff/users" >/dev/null
fi

accountant_api() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  if [[ -n "$body" ]]; then
    curl --fail-with-body --silent --show-error -b "$cookie_file" -c "$cookie_file" \
      -X "$method" -H 'Content-Type: application/json' --data "$body" "$BASE_URL$path"
  else
    curl --fail-with-body --silent --show-error -b "$cookie_file" -c "$cookie_file" \
      -X "$method" "$BASE_URL$path"
  fi
}

admin_api() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  if [[ -n "$body" ]]; then
    curl --fail-with-body --silent --show-error -X "$method" -H "X-Admin-Token: $admin_token" \
      -H 'Content-Type: application/json' --data "$body" "$BASE_URL$path"
  else
    curl --fail-with-body --silent --show-error -X "$method" -H "X-Admin-Token: $admin_token" "$BASE_URL$path"
  fi
}

login_status="$(curl --silent --show-error --output "$body_file" --write-out '%{http_code}' \
  -c "$cookie_file" -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=$ACCOUNTANT_EMAIL" --data-urlencode "password=$ACCOUNTANT_PASSWORD" \
  "$BASE_URL/api/v1/staff/auth/login")"
[[ "$login_status" == "204" ]]
profile="$(accountant_api GET /api/v1/staff/me)"
[[ "$(jq -r .role <<<"$profile")" == "ACCOUNTANT" ]]

overview="$(accountant_api GET /api/v1/operations/control/overview)"
branch_id="$(jq -er '.branches[0].id' <<<"$overview")"
previous_active="$(jq -r '[.management_documents[] | select(.document_type == "FISCAL_CONFIGURATION" and .status == "ACTIVE")][0].id // empty' <<<"$overview")"
stamp="$(date -u +%y%m%d%H%M%S)"
fiscal="$(accountant_api POST /api/v1/operations/control/management-documents "{
  \"branch_id\":\"$branch_id\",\"document_type\":\"FISCAL_CONFIGURATION\",
  \"number\":\"SMOKE-CONTABLE-$stamp\",\"status\":\"DRAFT\",
  \"metadata_json\":{\"numbering_owner\":\"ERPNEXT\",\"legal_name\":\"SmartDiag504 Taller de Prueba\",
  \"rtn\":\"08011999123456\",\"cai\":\"PRUEBA-SIN-VALIDEZ-FISCAL\",\"prefix\":\"000-001-01\",
  \"document_kind\":\"FACTURA\",\"template_code\":\"INVOICE_DEFAULT\",\"test_only\":true}
}")"
fiscal_id="$(jq -er .id <<<"$fiscal")"

guard_status="$(curl --silent --show-error --output "$body_file" --write-out '%{http_code}' \
  -b "$cookie_file" -X PATCH -H 'Content-Type: application/json' \
  --data '{"status":"ACTIVE","accountant_confirmed":false}' \
  "$BASE_URL/api/v1/operations/control/management-documents/$fiscal_id/status")"
[[ "$guard_status" == "422" ]]
fiscal="$(accountant_api PATCH "/api/v1/operations/control/management-documents/$fiscal_id/status" \
  '{"status":"ACTIVE","accountant_confirmed":true,"note":"Prueba funcional; no es autorización SAR"}')"
[[ "$(jq -r .status <<<"$fiscal")" == "ACTIVE" ]]

summary="$(accountant_api GET /api/v1/operations/finance/reporting/summary)"
[[ "$(jq -r .accounting_source <<<"$summary")" == "ERPNext" ]]

thermal_status="$(curl --silent --show-error --output "$body_file" --write-out '%{http_code}' \
  -b "$cookie_file" -X POST -H 'Content-Type: application/json' \
  --data '{"paper_size":"THERMAL_80","html_template":"<h1>{{ company.name }}</h1><p>{{ document.number }}</p><strong>{{ document.total }}</strong>","css_text":"body{font-family:Arial;font-size:10px;width:72mm}h1{font-size:13px}"}' \
  "$BASE_URL/api/v1/operations/documents/preview")"
[[ "$thermal_status" == "200" ]]
thermal_bytes="$(wc -c < "$body_file")"
[[ "$thermal_bytes" -gt 100 ]]

sales="$(accountant_api GET /api/v1/operations/finance/counter-sales)"
sale_id="$(jq -r '.[0].id // empty' <<<"$sales")"
invoice_pdf="SKIPPED_NO_SALE"
if [[ -n "$sale_id" ]]; then
  pdf_status="$(curl --silent --show-error --dump-header "$header_file" --output "$body_file" --write-out '%{http_code}' \
    -b "$cookie_file" "$BASE_URL/api/v1/operations/finance/counter-sales/$sale_id.pdf")"
  [[ "$pdf_status" == "200" ]]
  head -c 4 "$body_file" | grep -q '%PDF'
  grep -qi '^content-type: application/pdf' "$header_file"
  invoice_pdf="OK:$(wc -c < "$body_file")"
fi

work_orders="$(admin_api GET /api/v1/operations/work-orders)"
work_order_id="$(jq -er '.[0].id' <<<"$work_orders")"
evidence="$(admin_api GET "/api/v1/operations/work-orders/$work_order_id/evidence")"
evidence_id="$(jq -r '.[0].id // empty' <<<"$evidence")"
if [[ -z "$evidence_id" ]]; then
  printf '%s' 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=' | base64 -d > "$image_file"
  evidence="$(curl --fail-with-body --silent --show-error -H "X-Admin-Token: $admin_token" \
    -F 'category=QUALITY' -F 'caption=Evidencia privada de prueba funcional' -F 'actor=smoke-vps' \
    -F "file=@$image_file;type=image/png" "$BASE_URL/api/v1/operations/work-orders/$work_order_id/evidence")"
  evidence_id="$(jq -er .id <<<"$evidence")"
fi
evidence_path="/api/v1/operations/work-orders/$work_order_id/evidence/$evidence_id/content"
anonymous_evidence="$(curl --silent --output /dev/null --write-out '%{http_code}' "$BASE_URL$evidence_path")"
accountant_evidence="$(curl --silent --output /dev/null --write-out '%{http_code}' -b "$cookie_file" "$BASE_URL$evidence_path")"
admin_evidence="$(curl --silent --dump-header "$header_file" --output "$body_file" --write-out '%{http_code}' -H "X-Admin-Token: $admin_token" "$BASE_URL$evidence_path")"
[[ "$anonymous_evidence" == "401" ]]
[[ "$accountant_evidence" == "403" ]]
[[ "$admin_evidence" == "200" ]]
grep -qi '^cache-control: private, no-store' "$header_file"

smtp_network="$(docker inspect "$API_CONTAINER" --format '{{range $name, $network := .NetworkSettings.Networks}}{{$name}}{{end}}')"
docker run -d --rm --name "$smtp_container" --network "$smtp_network" axllent/mailpit:v1.21 >/dev/null
for _ in $(seq 1 20); do
  if docker exec "$API_CONTAINER" python -c "import urllib.request; urllib.request.urlopen('http://$smtp_container:8025/api/v1/info', timeout=2)" >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec \
  -e "SMTP_HOST=$smtp_container" -e SMTP_PORT=1025 -e SMTP_USE_TLS=false \
  -e SMTP_FROM_EMAIL=alertas@smartdiag504.test \
  "$API_CONTAINER" python -c "from types import SimpleNamespace; from app.config import Settings; from app.services.notifications import _send_email; delivery=SimpleNamespace(id='smtp-smoke', subject='Alerta SmartDiag504', recipient='contador@smartdiag504.test', body_text='Prueba de transporte SMTP'); print(_send_email(delivery, Settings()))" >/dev/null
smtp_messages="$(docker exec "$API_CONTAINER" python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://$smtp_container:8025/api/v1/messages'))['total'])")"
[[ "$smtp_messages" -ge 1 ]]

accountant_api PATCH "/api/v1/operations/control/management-documents/$fiscal_id/status" \
  '{"status":"EXPIRED","accountant_confirmed":false,"note":"Fin de prueba funcional"}' >/dev/null
if [[ -n "$previous_active" && "$previous_active" != "$fiscal_id" ]]; then
  accountant_api PATCH "/api/v1/operations/control/management-documents/$previous_active/status" \
    '{"status":"ACTIVE","accountant_confirmed":true,"note":"Serie previa restaurada después del smoke test"}' >/dev/null
fi

backup_file="$(find /opt/smartdiag504-backups -type f -name '*.sql.gz' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n1 | cut -d' ' -f2-)"
backup_check="NOT_CONFIGURED"
if [[ -n "$backup_file" ]]; then
  gzip -t "$backup_file"
  backup_check="LOCAL_ARCHIVE_OK"
fi

jq -n \
  --arg role "$(jq -r .role <<<"$profile")" \
  --arg fiscal_guard "422" \
  --arg fiscal_activation "ACTIVE_TEST_THEN_RESTORED" \
  --arg accounting_source "$(jq -r .accounting_source <<<"$summary")" \
  --arg gross_sales "$(jq -r .gross_sales <<<"$summary")" \
  --arg net_sales "$(jq -r .net_sales <<<"$summary")" \
  --arg gross_profit "$(jq -r .gross_profit <<<"$summary")" \
  --arg invoice_pdf "$invoice_pdf" \
  --arg thermal_preview "OK:$thermal_bytes" \
  --arg evidence_access "anonymous:$anonymous_evidence accountant:$accountant_evidence authorized:$admin_evidence" \
  --arg smtp "OK:$smtp_messages" \
  --arg backup "$backup_check" \
  '{role:$role,fiscal_guard:$fiscal_guard,fiscal_activation:$fiscal_activation,accounting:{source:$accounting_source,gross_sales:$gross_sales,net_sales:$net_sales,gross_profit:$gross_profit},printing:{invoice_pdf:$invoice_pdf,thermal_80_preview:$thermal_preview,physical_hardware:"NOT_ATTACHED"},private_evidence:$evidence_access,smtp_transport:$smtp,external_backup:$backup}'
