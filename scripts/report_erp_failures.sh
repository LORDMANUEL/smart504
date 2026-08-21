#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${BASE_URL:-https://taller.nexusmedi.org}"
API_CONTAINER="${API_CONTAINER:-platform-api-eeylxzuvyicq5i5lelcrcda9}"
TOKEN="$(docker exec "$API_CONTAINER" printenv ADMIN_API_TOKEN)"

curl --fail-with-body --silent --show-error \
  -H "X-Admin-Token: $TOKEN" \
  "$BASE_URL/api/v1/operations/integrations/erp/jobs?status=FAILED" \
  | jq '[.[] | {id, aggregate_type, aggregate_id, operation, attempts, last_error, created_at}][0:20]'
