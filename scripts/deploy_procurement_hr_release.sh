#!/usr/bin/env bash
set -Eeuo pipefail

repo=/opt/smartdiag504-demo
coolify=/data/coolify/services/eeylxzuvyicq5i5lelcrcda9/docker-compose.yml
runtime=$repo/infra/coolify/runtime-upgrade.override.yaml
erp=/opt/smartdiag504-erpnext
stamp=20260817-procurement-hr-formats
main=(docker compose -p eeylxzuvyicq5i5lelcrcda9 -f "$coolify" -f "$runtime")
erp_compose=(docker compose -p smartdiag504-erp -f "$erp/compose.generated.yml" -f "$erp/compose.coolify.override.yml")

test -s "/opt/smartdiag504-backups/pre-$stamp-deb/platform.sql.gz"
"${erp_compose[@]}" exec -T backend bench --site erp.nexusmedi.org backup --with-files

docker tag smartdiag504-demo-platform-api:latest "smartdiag504-demo-platform-api:pre-$stamp"
docker tag smartdiag504-demo-ops-web:latest "smartdiag504-demo-ops-web:pre-$stamp"
docker tag smartdiag504-erpnext-workshop:20 "smartdiag504-erpnext-workshop:pre-$stamp"

docker build -t smartdiag504-demo-platform-api:latest -f "$repo/services/platform-api/Dockerfile" "$repo"
docker tag smartdiag504-ops-web:procurement-hr-20260817 smartdiag504-demo-ops-web:latest
docker build --build-arg "BASE_IMAGE=smartdiag504-erpnext-workshop:pre-$stamp" -t smartdiag504-erpnext-workshop:20 -f "$repo/infra/erpnext/Dockerfile.workshop-update" "$repo"

"${main[@]}" run --rm migrate
"${main[@]}" up -d --force-recreate platform-api erp-sync-worker notification-worker ops-web gateway

"${erp_compose[@]}" up -d --force-recreate backend queue-short queue-long scheduler websocket frontend
"${erp_compose[@]}" exec -T backend bench --site erp.nexusmedi.org migrate

echo 'deployment-procurement-hr-release-ok'
