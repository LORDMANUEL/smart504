#!/usr/bin/env bash
set -Eeuo pipefail

INTERVAL=${BACKUP_INTERVAL_SECONDS:-21600}
RETENTION_DAYS=${LOCAL_BACKUP_RETENTION_DAYS:-7}
mkdir -p /backups

perform_backup() {
  local stamp bundle
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  bundle="/backups/${stamp}"
  mkdir -p "${bundle}/metadata"

  PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    --host="${POSTGRES_HOST}" --port="${POSTGRES_PORT:-5432}" \
    --username="${POSTGRES_USER}" --format=custom --no-owner \
    --file="${bundle}/platform.pgdump" "${POSTGRES_DB}"

  mariadb-dump \
    --host="${MARIADB_HOST}" --port="${MARIADB_PORT:-3306}" \
    --user=root --password="${MARIADB_ROOT_PASSWORD}" \
    --single-transaction --routines --events --all-databases \
    | zstd -T0 -10 > "${bundle}/erpnext-all.sql.zst"

  tar --zstd -cf "${bundle}/frappe-sites.tar.zst" -C /source/frappe-sites .
  tar --zstd -cf "${bundle}/platform-media.tar.zst" -C /source/platform-media .
  tar --zstd -cf "${bundle}/garage-config.tar.zst" -C /source/garage-config .
  tar --zstd -cf "${bundle}/garage-meta.tar.zst" -C /source/garage-meta .
  tar --zstd -cf "${bundle}/garage-data.tar.zst" -C /source/garage-data .
  printf '{"schema_version":1,"created_at":"%s","components":["postgres","mariadb","frappe-sites","platform-media","garage-config","garage-meta","garage-data"]}\n' \
    "$(date -u +%FT%TZ)" > "${bundle}/metadata/backup.json"
  (cd "${bundle}" && find . -type f ! -name manifest.sha256 -print0 | sort -z | xargs -0 sha256sum > manifest.sha256)

  if [[ -n "${RESTIC_REPOSITORY:-}" ]]; then
    : "${RESTIC_PASSWORD:?RESTIC_PASSWORD is required when RESTIC_REPOSITORY is set}"
    restic snapshots >/dev/null 2>&1 || restic init
    restic backup "${bundle}" --tag smartdiag504
    restic forget --keep-daily 7 --keep-weekly 5 --keep-monthly 12 --prune
  fi

  find /backups -mindepth 1 -maxdepth 1 -type d -mtime "+${RETENTION_DAYS}" -exec rm -rf {} +
  printf '%s\n' "${stamp}" > /backups/LAST_SUCCESS
  echo "Backup completed: ${stamp}"
}

if [[ "${RUN_ONCE:-0}" == "1" ]]; then
  perform_backup
  exit 0
fi

while true; do
  perform_backup || echo "Backup attempt failed at $(date -u +%FT%TZ)" >&2
  sleep "${INTERVAL}"
done
