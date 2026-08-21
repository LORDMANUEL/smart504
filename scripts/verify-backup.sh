#!/usr/bin/env bash
set -Eeuo pipefail

ARCHIVE=${1:-}
[[ -n "${ARCHIVE}" && -f "${ARCHIVE}" ]] || { echo "Usage: $0 ARCHIVE.tar.gz" >&2; exit 2; }
work=$(mktemp -d)
trap 'rm -rf "${work}"' EXIT
tar -xzf "${ARCHIVE}" -C "${work}"
bundle=$(find "${work}" -mindepth 1 -maxdepth 1 -type d | head -1)
[[ -n "${bundle}" && -f "${bundle}/manifest.sha256" ]] || { echo "ERROR: backup manifest missing." >&2; exit 1; }
(cd "${bundle}" && sha256sum -c manifest.sha256)
for required in platform.pgdump erpnext-all.sql.zst frappe-sites.tar.zst platform-media.tar.zst garage-config.tar.zst garage-meta.tar.zst garage-data.tar.zst metadata/backup.json; do
  [[ -s "${bundle}/${required}" ]] || { echo "ERROR: backup component missing: ${required}" >&2; exit 1; }
done
echo "Backup integrity passed: ${ARCHIVE}"
