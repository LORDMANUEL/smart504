#!/usr/bin/env bash
set -Eeuo pipefail

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "Docker Engine and Compose v2 are already installed."
  exit 0
fi

[[ -r /etc/os-release ]] || { echo "ERROR: /etc/os-release is unavailable." >&2; exit 1; }
# shellcheck disable=SC1091
source /etc/os-release
case "${ID:-}" in
  ubuntu|debian) ;;
  *) echo "ERROR: automatic Docker installation supports Debian and Ubuntu only. Install Docker Engine 23+ and Compose v2 manually." >&2; exit 1 ;;
esac

if [[ ${EUID} -eq 0 ]]; then
  SUDO=()
elif command -v sudo >/dev/null 2>&1; then
  SUDO=(sudo)
else
  echo "ERROR: run as root or install sudo before automatic Docker setup." >&2
  exit 1
fi

"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y ca-certificates curl gnupg git jq unzip
"${SUDO[@]}" install -m 0755 -d /etc/apt/keyrings
curl -fsSL "https://download.docker.com/linux/${ID}/gpg" | "${SUDO[@]}" gpg --dearmor -o /etc/apt/keyrings/docker.gpg
"${SUDO[@]}" chmod a+r /etc/apt/keyrings/docker.gpg
arch=$(dpkg --print-architecture)
repo_codename=${VERSION_CODENAME:-}
[[ -n "${repo_codename}" ]] || { echo "ERROR: VERSION_CODENAME is missing from /etc/os-release." >&2; exit 1; }
printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/%s %s stable\n' \
  "${arch}" "${ID}" "${repo_codename}" \
  | "${SUDO[@]}" tee /etc/apt/sources.list.d/docker.list >/dev/null
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
"${SUDO[@]}" systemctl enable --now docker

if [[ ${EUID} -ne 0 ]]; then
  "${SUDO[@]}" usermod -aG docker "${USER}"
  echo "Docker was installed. Log out and back in so the docker group applies, then rerun install-vps.sh."
  exit 2
fi

docker version >/dev/null
docker compose version >/dev/null
echo "Docker Engine and Compose v2 installed."
