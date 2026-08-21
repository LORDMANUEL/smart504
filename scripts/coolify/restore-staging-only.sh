#!/usr/bin/env bash
set -Eeuo pipefail

environment_name="${1:?Usage: restore-staging-only.sh smartdiag504-restore-YYYYMMDD /backup/path}"
backup_dir="${2:?Usage: restore-staging-only.sh smartdiag504-restore-YYYYMMDD /backup/path}"
[[ "${environment_name}" == smartdiag504-restore-* ]] || { echo "ERROR: destination must be a dedicated restore staging" >&2; exit 2; }
[[ "${CONFIRM_RESTORE_ENVIRONMENT:-}" == "${environment_name}" ]] || {
  echo "ERROR: set CONFIRM_RESTORE_ENVIRONMENT to the exact staging name" >&2; exit 2;
}
"$(dirname "$0")/backup-verify.sh" "${backup_dir}"
echo "Guard checks passed for ${environment_name}."
echo "Restore through the dedicated Coolify staging resource using docs/deployment/COOLIFY_BACKUP_RESTORE.md."
echo "No database or volume was modified by this guard script."
