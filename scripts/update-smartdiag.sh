#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/.env}"
cd "$ROOT_DIR"
[[ -f "$ENV_FILE" ]] || { echo "ERROR: falta $ENV_FILE" >&2; exit 1; }
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || { echo "ERROR: hay cambios locales; guárdelos antes de actualizar." >&2; exit 1; }

current="$(git rev-parse HEAD)"
git fetch --tags origin
target="${1:-origin/main}"
git rev-parse --verify "$target" >/dev/null
backup_dir="/var/backups/smartdiag504/update-$(date -u +%Y%m%dT%H%M%SZ)"
install -d -m 0700 "$backup_dir"
install -m 0600 "$ENV_FILE" "$backup_dir/environment.backup"
git pull --ff-only origin "${target#origin/}"

if ! bash scripts/install-vps.sh --env-file "$ENV_FILE" --skip-docker-install --observability; then
  echo "ERROR: actualización falló. Código anterior: $current" >&2
  echo "Para volver: git checkout $current && bash scripts/install-vps.sh --env-file $ENV_FILE --skip-docker-install" >&2
  exit 1
fi
echo "Actualización completada: $(git rev-parse --short HEAD)"
