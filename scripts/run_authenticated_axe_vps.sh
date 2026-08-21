#!/usr/bin/env bash
set -Eeuo pipefail

repo="${SMARTDIAG_REPO:-/opt/smartdiag504-demo}"
password="${STAFF_E2E_PASSWORD:-Rol-E2E-Seguro-504!}"
base_url="${QA_BASE_URL:-https://taller.nexusmedi.org}"
api_container="${API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
admin_token="$(docker exec "$api_container" printenv ADMIN_API_TOKEN)"
stamp="$(date -u +%y%m%d%H%M%S)"
overview="$(curl --fail-with-body --silent --show-error -H "X-Admin-Token: $admin_token" \
  "$base_url/api/v1/operations/control/overview")"
branch_id="$(jq -er '.branches[] | select(.code == "MAIN") | .id' <<<"$overview")"
role_users='{}'

for role in OWNER ADMIN MANAGER RECEPTION TECHNICIAN WAREHOUSE CASHIER ACCOUNTANT MARKETING AUDITOR; do
  role_lower="$(tr '[:upper:]' '[:lower:]' <<<"$role")"
  email="acceptance.$role_lower.$stamp@nexusmedi.org"
  payload="$(jq -n --arg email "$email" --arg password "$password" --arg role "$role" \
    --arg branch "$branch_id" --arg code "${role:0:3}-$stamp" \
    '{email:$email,password:$password,employee_code:$code,full_name:("Aceptación " + $role),role:$role,permissions_json:[],is_active:true,is_superuser:false,is_verified:true,branch_id:$branch}')"
  curl --fail-with-body --silent --show-error -H "X-Admin-Token: $admin_token" \
    -H 'Content-Type: application/json' --data "$payload" "$base_url/api/v1/staff/users" >/dev/null
  role_users="$(jq -c --arg role "$role" --arg email "$email" '. + {($role):$email}' <<<"$role_users")"
done

docker run --rm --ipc=host \
  -v "$repo:/workspace" \
  -w /tmp/qa \
  -e QA_STAFF_PASSWORD="$password" \
  -e QA_ROLE_USERS="$role_users" \
  -e QA_BASE_URL="$base_url" \
  mcr.microsoft.com/playwright:v1.54.0-noble \
  bash -lc 'npm init -y >/dev/null && npm install --silent playwright@1.54.0 @axe-core/playwright && cp /workspace/scripts/qa_authenticated_axe.mjs ./qa_authenticated_axe.mjs && node ./qa_authenticated_axe.mjs'
