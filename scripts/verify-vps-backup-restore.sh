#!/usr/bin/env bash
set -Eeuo pipefail

runner="${SMARTDIAG_BACKUP_CONTAINER:-smartdiag504-backup-runner}"
image="${SMARTDIAG_BACKUP_IMAGE:-smartdiag504-backup-runner:current}"
network="smartdiag504-restore-validation"
pg_container="smartdiag504-restore-postgres"
my_container="smartdiag504-restore-mariadb"
test_password="restore-validation-only"

cleanup() {
  docker rm -f "$pg_container" "$my_container" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
}
trap cleanup EXIT

stamp="$(docker exec "$runner" sh -lc 'cat /backups/LAST_SUCCESS')"
docker exec "$runner" sh -lc "cd /backups/$stamp && sha256sum -c manifest.sha256"

cleanup
docker network create "$network" >/dev/null
docker run -d --name "$pg_container" --network "$network" --tmpfs /var/lib/postgresql/data \
  -e POSTGRES_PASSWORD="$test_password" postgres:17-alpine >/dev/null
docker run -d --name "$my_container" --network "$network" --tmpfs /var/lib/mysql \
  -e MARIADB_ROOT_PASSWORD="$test_password" mariadb:11.8 >/dev/null

for _ in $(seq 1 60); do
  docker exec "$pg_container" pg_isready -U postgres >/dev/null 2>&1 && break
  sleep 1
done
for _ in $(seq 1 90); do
  docker exec "$my_container" mariadb-admin ping -uroot -p"$test_password" --silent >/dev/null 2>&1 && break
  sleep 1
done
docker exec "$pg_container" pg_isready -U postgres >/dev/null
docker exec "$my_container" mariadb-admin ping -uroot -p"$test_password" --silent >/dev/null

docker run --rm --entrypoint bash --network "$network" -e PGPASSWORD="$test_password" \
  -v smartdiag504_backup-data:/backups:ro "$image" \
  -lc "createdb -h $pg_container -U postgres smartdiag_restore && pg_restore -h $pg_container -U postgres -d smartdiag_restore --no-owner /backups/$stamp/platform.pgdump && psql -h $pg_container -U postgres -d smartdiag_restore -Atc 'select count(*) from alembic_version'"

docker run --rm --entrypoint bash --network "$network" -v smartdiag504_backup-data:/backups:ro "$image" \
  -lc "zstdcat /backups/$stamp/erpnext-all.sql.zst | mariadb -h $my_container -uroot -p'$test_password' && mariadb -h $my_container -uroot -p'$test_password' -Nse 'show databases' | grep -Ev '^(information_schema|mysql|performance_schema|sys)$' | grep -q ."

printf 'Isolated restore validated for backup %s\n' "$stamp"
