#!/usr/bin/env bash
set -Eeuo pipefail

BACKUP_ROOT=${BACKUP_ROOT:-/var/backups/smartdiag504-local}
RETENTION_DAYS=${RETENTION_DAYS:-14}
case "${BACKUP_ROOT}" in
  /var/backups/smartdiag504-local|/var/backups/smartdiag504-local/*) ;;
  *) echo "ERROR: BACKUP_ROOT debe permanecer dentro de /var/backups/smartdiag504-local" >&2; exit 2 ;;
esac
stamp=$(date -u +%Y%m%dT%H%M%SZ)
target="${BACKUP_ROOT}/${stamp}"
install -d -m 0700 "${target}"

postgres=$(docker ps --format '{{.Names}}' | grep '^postgres-ylntoi' | head -n1)
mariadb=$(docker ps --format '{{.Names}}' | grep '^mariadb-ylntoi' | head -n1)
frappe=$(docker ps --format '{{.Names}}' | grep '^frappe-backend-ylntoi' | head -n1)
garage=$(docker ps --format '{{.Names}}' | grep '^garage-rassuij' | head -n1)
[[ -n "${postgres}" && -n "${mariadb}" && -n "${frappe}" && -n "${garage}" ]]

pg_user=$(docker exec "${postgres}" printenv POSTGRES_USER)
pg_db=$(docker exec "${postgres}" printenv POSTGRES_DB)
docker exec "${postgres}" pg_dump -U "${pg_user}" -d "${pg_db}" -Fc > "${target}/platform.pgdump"

docker exec "${mariadb}" sh -lc 'mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" --all-databases --single-transaction --routines --events' | gzip -9 > "${target}/erpnext-all.sql.gz"
docker exec "${frappe}" tar -C /home/frappe/frappe-bench -czf - sites > "${target}/frappe-sites.tar.gz"

garage_volume=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/var/lib/garage"}}{{.Name}}{{end}}{{end}}' "${garage}")
[[ -n "${garage_volume}" ]]
docker run --rm -v "${garage_volume}:/source:ro" alpine:3.22 tar -C /source -czf - . > "${target}/garage-data.tar.gz"

(cd "${target}" && sha256sum platform.pgdump erpnext-all.sql.gz frappe-sites.tar.gz garage-data.tar.gz > manifest.sha256)
(cd "${target}" && sha256sum -c manifest.sha256)
gzip -t "${target}/erpnext-all.sql.gz" "${target}/frappe-sites.tar.gz" "${target}/garage-data.tar.gz"

restore_db="smartdiag_restore_${stamp,,}"
restore_db=${restore_db//[^a-z0-9_]/_}
docker exec "${postgres}" createdb -U "${pg_user}" "${restore_db}"
trap 'docker exec "${postgres}" dropdb -U "${pg_user}" --if-exists "${restore_db}" >/dev/null 2>&1 || true' EXIT
docker exec -i "${postgres}" pg_restore -U "${pg_user}" -d "${restore_db}" --no-owner --no-privileges < "${target}/platform.pgdump"
table_count=$(docker exec "${postgres}" psql -U "${pg_user}" -d "${restore_db}" -Atc "select count(*) from information_schema.tables where table_schema='public';")
[[ "${table_count}" -gt 0 ]]
docker exec "${postgres}" dropdb -U "${pg_user}" "${restore_db}"
trap - EXIT

printf 'snapshot=%s\nplatform_restore_tables=%s\ncreated_at=%s\n' "${stamp}" "${table_count}" "$(date -u +%FT%TZ)" > "${target}/VERIFIED"
ln -sfn "${target}" "${BACKUP_ROOT}/latest"
find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d -mtime "+${RETENTION_DAYS}" -exec rm -rf -- {} +
echo "Snapshot local verificado: ${target} (${table_count} tablas restauradas)"
