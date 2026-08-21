#!/usr/bin/env bash
set -Eeuo pipefail

backup_dir="${1:?Usage: backup-verify.sh /absolute/backup/directory}"
[[ "${backup_dir}" = /* ]] || { echo "ERROR: absolute path required" >&2; exit 2; }
[[ -d "${backup_dir}" ]] || { echo "ERROR: backup directory does not exist" >&2; exit 2; }
[[ -f "${backup_dir}/manifest.sha256" ]] || { echo "ERROR: manifest.sha256 is missing" >&2; exit 2; }

(cd "${backup_dir}" && sha256sum --check manifest.sha256)
for required in metadata.json postgres frappe s3; do
  [[ -e "${backup_dir}/${required}" ]] || { echo "ERROR: missing ${required}" >&2; exit 3; }
done
echo "Backup manifest and required components are valid. This does not replace a restore drill."
