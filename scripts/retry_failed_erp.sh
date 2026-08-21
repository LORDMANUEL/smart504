#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${BASE_URL:-https://taller.nexusmedi.org}"
API_CONTAINER="${API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
TOKEN="$(docker exec "$API_CONTAINER" printenv ADMIN_API_TOKEN)"
jobs="$(curl --fail-with-body --silent --show-error -H "X-Admin-Token: $TOKEN" "$BASE_URL/api/v1/operations/integrations/erp/jobs?status=FAILED")"

while IFS= read -r job_id; do
  [[ -z "$job_id" ]] && continue
  curl --fail-with-body --silent --show-error -X POST \
    -H "X-Admin-Token: $TOKEN" -H 'Content-Type: application/json' \
    --data '{}' "$BASE_URL/api/v1/operations/integrations/erp/jobs/$job_id/retry" >/dev/null
done < <(jq -r '.[].id' <<<"$jobs")

curl --fail-with-body --silent --show-error -X POST \
  -H "X-Admin-Token: $TOKEN" -H 'Content-Type: application/json' \
  --data '{}' "$BASE_URL/api/v1/operations/integrations/erp/process" | jq .
