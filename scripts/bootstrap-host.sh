#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR=${SMARTDIAG_APP_DIR:-/opt/smartdiag504}
APP_USER=${SMARTDIAG_APP_USER:-${SUDO_USER:-${USER:-root}}}
OPEN_FIREWALL=${ENABLE_UFW:-0}
SKIP_DOCKER=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-dir) APP_DIR="$2"; shift 2 ;;
    --app-user) APP_USER="$2"; shift 2 ;;
    --open-firewall) OPEN_FIREWALL=1; shift ;;
    --skip-docker) SKIP_DOCKER=1; shift ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/bootstrap-host.sh [options]
  --app-dir PATH       Installation directory (default /opt/smartdiag504)
  --app-user USER      Owner/operator account (default invoking sudo user)
  --open-firewall      Enable UFW and allow SSH, TCP 80/443 and UDP 443
  --skip-docker        Install host utilities only
USAGE
      exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; exit 2 ;;
  esac
done

[[ -r /etc/os-release ]] || { echo "ERROR: /etc/os-release is unavailable." >&2; exit 1; }
# shellcheck disable=SC1091
source /etc/os-release
case "${ID:-}" in
  ubuntu|debian) ;;
  *) echo "ERROR: supported automatic host bootstrap: Debian or Ubuntu." >&2; exit 1 ;;
esac

if [[ ${EUID} -eq 0 ]]; then
  SUDO=()
elif command -v sudo >/dev/null 2>&1; then
  SUDO=(sudo)
else
  echo "ERROR: run as root or install sudo." >&2
  exit 1
fi

getent passwd "${APP_USER}" >/dev/null 2>&1 || {
  echo "ERROR: application user '${APP_USER}' does not exist." >&2
  exit 1
}

"${SUDO[@]}" apt-get update
DEBIAN_FRONTEND=noninteractive "${SUDO[@]}" apt-get install -y \
  ca-certificates curl git jq unzip zip rsync age restic openssl python3 ufw

if [[ ${SKIP_DOCKER} -eq 0 ]]; then
  "${ROOT_DIR}/scripts/install-docker.sh"
  "${SUDO[@]}" usermod -aG docker "${APP_USER}"
fi

"${SUDO[@]}" install -d -m 0750 -o "${APP_USER}" -g "${APP_USER}" "${APP_DIR}"
"${SUDO[@]}" install -d -m 0700 -o "${APP_USER}" -g "${APP_USER}" /var/backups/smartdiag504

sysctl_file=/etc/sysctl.d/99-smartdiag504.conf
cat <<'SYSCTL' | "${SUDO[@]}" tee "${sysctl_file}" >/dev/null
# SmartDiag504 container host defaults.
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 1024
vm.overcommit_memory = 1
SYSCTL
"${SUDO[@]}" sysctl --system >/dev/null

if [[ ${OPEN_FIREWALL} -eq 1 ]]; then
  "${SUDO[@]}" ufw allow OpenSSH
  "${SUDO[@]}" ufw allow 80/tcp
  "${SUDO[@]}" ufw allow 443/tcp
  "${SUDO[@]}" ufw allow 443/udp
  "${SUDO[@]}" ufw --force enable
fi

if command -v docker >/dev/null 2>&1; then
  "${SUDO[@]}" systemctl enable --now docker
  "${SUDO[@]}" docker version >/dev/null
  "${SUDO[@]}" docker compose version >/dev/null
fi

cat <<REPORT
Host bootstrap completed.
Application directory: ${APP_DIR}
Operator account: ${APP_USER}
Firewall configured: ${OPEN_FIREWALL}

When this command added your current account to the docker group, start a new login session before running Docker without sudo. The first guided installation may continue as root.
REPORT
