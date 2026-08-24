#!/usr/bin/env bash
set -Eeuo pipefail

repo="${SMARTDIAG_REPO:-/opt/smartdiag504}"
app_network="${SMARTDIAG_APP_NETWORK:-ylntoiwps359inz3catqyo1s}"
postgres_container="${SMARTDIAG_POSTGRES_CONTAINER:-postgres-ylntoiwps359inz3catqyo1s-134556722051}"
mariadb_container="${SMARTDIAG_MARIADB_CONTAINER:-mariadb-ylntoiwps359inz3catqyo1s-134556952375}"
runner="${SMARTDIAG_BACKUP_CONTAINER:-smartdiag504-backup-runner}"
image="${SMARTDIAG_BACKUP_IMAGE:-smartdiag504-backup-runner:current}"

required_containers=("$postgres_container" "$mariadb_container")
for container in "${required_containers[@]}"; do
  docker inspect "$container" >/dev/null
done
docker network inspect "$app_network" >/dev/null

postgres_db="$(docker exec "$postgres_container" printenv POSTGRES_DB)"
postgres_user="$(docker exec "$postgres_container" printenv POSTGRES_USER)"
postgres_password="$(docker exec "$postgres_container" printenv POSTGRES_PASSWORD)"
mariadb_password="$(docker exec "$mariadb_container" printenv MARIADB_ROOT_PASSWORD)"

docker build -f "$repo/infra/backup/Dockerfile" -t "$image" "$repo"
docker volume create smartdiag504_backup-data >/dev/null
docker rm -f "$runner" >/dev/null 2>&1 || true
docker run -d \
  --name "$runner" \
  --restart unless-stopped \
  --network "$app_network" \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_DB="$postgres_db" \
  -e POSTGRES_USER="$postgres_user" \
  -e POSTGRES_PASSWORD="$postgres_password" \
  -e MARIADB_HOST=mariadb \
  -e MARIADB_ROOT_PASSWORD="$mariadb_password" \
  -e BACKUP_INTERVAL_SECONDS="${BACKUP_INTERVAL_SECONDS:-21600}" \
  -e LOCAL_BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}" \
  -v smartdiag504_backup-data:/backups \
  -v ylntoiwps359inz3catqyo1s_frappe-sites:/source/frappe-sites:ro \
  -v ylntoiwps359inz3catqyo1s_platform-media:/source/platform-media:ro \
  -v rassuijrunophcaxpddctxvp_garage-config:/source/garage-config:ro \
  -v rassuijrunophcaxpddctxvp_garage-meta:/source/garage-meta:ro \
  -v rassuijrunophcaxpddctxvp_garage-data:/source/garage-data:ro \
  "$image" >/dev/null

printf 'Backup runner started: %s\n' "$runner"
