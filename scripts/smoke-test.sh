#!/usr/bin/env bash
set -Eeuo pipefail

ENV_FILE=${1:-.env}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
# shellcheck source=scripts/lib/common.sh
source "${ROOT_DIR}/scripts/lib/common.sh"
smartdiag_require_env_file "${ENV_FILE}"
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a
API_BASE=$(smartdiag_url "${SMOKE_API_URL:-${API_SITE_ADDRESS:-http://localhost:8082}}")
PUBLIC_BASE=$(smartdiag_url "${SMOKE_BASE_URL:-${PUBLIC_SITE_ADDRESS:-http://localhost}}")
OPS_BASE=$(smartdiag_url "${SMOKE_OPS_URL:-${OPS_SITE_ADDRESS:-http://localhost:8081}}")
ERP_BASE=$(smartdiag_url "${SMOKE_ERP_URL:-${ERP_SITE_ADDRESS:-}}")

tmp=$(mktemp -d)
trap 'rm -rf "${tmp}"' EXIT

curl -fsS --max-time 20 "${API_BASE}/health" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="ok"'
curl -fsS --max-time 20 "${API_BASE}/ready" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="ready"'
curl -fsS --max-time 20 "${API_BASE}/api/v1/catalog/products" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert isinstance(d,list) and len(d)>=1'
curl -fsS --max-time 20 -H "X-Admin-Token: ${ADMIN_API_TOKEN}" \
  "${API_BASE}/api/v1/operations/work-orders/board" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); cols=d.get("columns",d); assert [x["status"] for x in cols]==["CREATED","QUOTED_BY_TECHNICIAN","PENDING_CUSTOMER_APPROVAL","PENDING_PARTS","READY_TO_INVOICE","INVOICED"]'
curl -fsS --max-time 20 -H "X-Admin-Token: ${ADMIN_API_TOKEN}" \
  "${API_BASE}/api/v1/admin/store/orders" \
  | python3 -c 'import json,sys; assert isinstance(json.load(sys.stdin),list)'

curl -fsS --max-time 20 -X POST "${API_BASE}/api/v1/chat/sessions" \
  -H 'Content-Type: application/json' \
  --data '{"locale":"es-HN","accepted_privacy":true}' > "${tmp}/session.json"
read -r session_id session_token < <(python3 - "${tmp}/session.json" <<'PY'
import json,sys
value=json.load(open(sys.argv[1],encoding='utf-8'))
print(value['session_id'], value['session_token'])
PY
)
curl -fsS --max-time 30 -X POST "${API_BASE}/api/v1/chat/sessions/${session_id}/messages" \
  -H 'Content-Type: application/json' \
  -H "X-Chat-Session-Token: ${session_token}" \
  --data '{"message":"¿Cómo reservo un diagnóstico?","client_message_id":"smoke-test-message-0001"}' \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["assistant_message"]["content"]; assert d["mode"]'

curl -fsS --max-time 20 "${PUBLIC_BASE}/" | grep -qi 'SmartDiag504'
curl -fsS --max-time 20 "${OPS_BASE}/" | grep -qi 'SmartDiag504'
if [[ -n "${ERP_BASE}" && "${SKIP_ERP_SMOKE:-0}" != "1" ]]; then
  curl -fsS --max-time 30 "${ERP_BASE}/api/method/ping" >/dev/null
fi

echo "Smoke tests passed: API readiness, catalog, store orders, six-stage OT board, chatbot, public site, operations site and ERP ping."
