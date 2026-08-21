#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${ROOT_DIR}/apps/public-web/public/images/stock"
MODE="download"

case "${1:-}" in
  "") ;;
  --check) MODE="check" ;;
  --require-local) MODE="require-local" ;;
  -h|--help) echo "Usage: $0 [--check|--require-local]"; exit 0 ;;
  *) echo "Usage: $0 [--check|--require-local]" >&2; exit 2 ;;
esac

mkdir -p "${TARGET_DIR}"

declare -A URLS=(
  [workshop-hero.jpg]='https://commons.wikimedia.org/wiki/Special:Redirect/file/Auto_workshop01.jpg?width=1600'
  [diagnostic-service.jpg]='https://commons.wikimedia.org/wiki/Special:Redirect/file/Mechanic_repairing_car_engine.jpg?width=1400'
  [engine-service.jpg]='https://commons.wikimedia.org/wiki/Special:Redirect/file/Auto_workshop02.jpg?width=1400'
  [technician-work.jpg]='https://commons.wikimedia.org/wiki/Special:Redirect/file/Mechanic_repairing_car_engine_1.jpg?width=1400'
)

validate_jpeg() {
  local path=$1
  [[ -s "${path}" ]] || return 1
  [[ $(stat -c %s "${path}") -ge 30000 ]] || return 1
  [[ $(od -An -tx1 -N2 "${path}" | tr -d ' \n') == ffd8 ]] || return 1
}

write_attribution() {
  cat > "${TARGET_DIR}/ATTRIBUTION.md" <<'ATTRIBUTION'
# Fotografías públicas SmartDiag504

Estas son fotografías reales existentes, no generadas por IA. El instalador las descarga desde Wikimedia Commons y las sirve localmente para no depender de terceros en cada visita.

- `workshop-hero.jpg`: **Auto workshop01.jpg**, Leotard — dominio público. Fuente: https://commons.wikimedia.org/wiki/File:Auto_workshop01.jpg
- `diagnostic-service.jpg`: **Mechanic repairing car engine.jpg**, Bembety — CC0 1.0. Fuente: https://commons.wikimedia.org/wiki/File:Mechanic_repairing_car_engine.jpg
- `engine-service.jpg`: **Auto workshop02.jpg**, Leotard — dominio público. Fuente: https://commons.wikimedia.org/wiki/File:Auto_workshop02.jpg
- `technician-work.jpg`: **Mechanic repairing car engine 1.jpg**, Bembety — CC0 1.0. Fuente: https://commons.wikimedia.org/wiki/File:Mechanic_repairing_car_engine_1.jpg

SmartDiag504 puede reemplazar estos archivos, conservando exactamente los mismos nombres, por fotografías propias del taller sin recompilar la aplicación.
ATTRIBUTION
}

for file in "${!URLS[@]}"; do
  url="${URLS[${file}]}"
  [[ "${url}" == https://commons.wikimedia.org/* ]] || { echo "Invalid source URL for ${file}" >&2; exit 1; }
  destination="${TARGET_DIR}/${file}"

  if validate_jpeg "${destination}"; then
    echo "Asset OK: ${file}"
    continue
  fi
  if [[ ${MODE} == check ]]; then
    echo "Remote real-photo asset configured; installer will fetch: ${file}"
    continue
  fi
  if [[ ${MODE} == require-local ]]; then
    echo "Missing or invalid local asset: ${file}" >&2
    exit 1
  fi

  command -v curl >/dev/null 2>&1 || { echo "curl is required to download public assets" >&2; exit 1; }
  temporary="${destination}.part"
  rm -f "${temporary}"
  echo "Downloading real licensed photograph: ${file}"
  curl --fail --location --retry 4 --retry-delay 2 --connect-timeout 15 --max-time 180 \
    --user-agent 'SmartDiag504-AssetFetcher/0.4' "${url}" -o "${temporary}"
  validate_jpeg "${temporary}" || {
    rm -f "${temporary}"
    echo "Downloaded file failed JPEG validation: ${file}" >&2
    exit 1
  }
  mv "${temporary}" "${destination}"
done

write_attribution
echo "Public photography asset contract ready in ${TARGET_DIR}"
