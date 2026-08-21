#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
DRY_RUN=0
NON_INTERACTIVE=0
ENABLE_AI=1
ENABLE_OBSERVABILITY=1
OPEN_FIREWALL=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --without-ai) ENABLE_AI=0; shift ;;
    --without-observability) ENABLE_OBSERVABILITY=0; shift ;;
    --no-firewall) OPEN_FIREWALL=0; shift ;;
    -h|--help)
      cat <<'HELP'
Uso: sudo bash install.sh [opciones]

  --dry-run                 Valida las respuestas sin instalar ni iniciar Docker
  --non-interactive         Usa SMARTDIAG_* del entorno; no muestra formularios
  --env-file RUTA           Archivo de configuración (predeterminado: .env)
  --without-ai              No inicia Ollama/ChromaDB local
  --without-observability   No inicia Prometheus/Grafana
  --no-firewall             No configura UFW

Variables no interactivas:
  SMARTDIAG_BASE_DOMAIN, SMARTDIAG_SERVER_IP, SMARTDIAG_ACME_EMAIL,
  SMARTDIAG_BUSINESS_NAME, SMARTDIAG_PHONE, SMARTDIAG_ADDRESS.
HELP
      exit 0 ;;
    *) echo "ERROR: opción desconocida: $1" >&2; exit 2 ;;
  esac
done

[[ -r /etc/os-release ]] || { echo "ERROR: Linux con /etc/os-release es obligatorio." >&2; exit 1; }
# shellcheck disable=SC1091
source /etc/os-release
case "${ID:-}" in ubuntu|debian) ;; *) echo "ERROR: use Debian 12 o Ubuntu 24.04." >&2; exit 1 ;; esac

if command -v whiptail >/dev/null 2>&1 && [[ -t 1 && ${NON_INTERACTIVE} -eq 0 ]]; then
  UI=whiptail
else
  UI=plain
fi

message() {
  local title="$1" body="$2"
  if [[ "$UI" == whiptail ]]; then whiptail --title "$title" --msgbox "$body" 18 78
  else printf '\n%s\n%s\n\n' "=== $title ===" "$body"; fi
}

ask() {
  local title="$1" prompt="$2" default="$3" value
  if [[ ${NON_INTERACTIVE} -eq 1 ]]; then printf '%s' "$default"; return; fi
  if [[ "$UI" == whiptail ]]; then
    value="$(whiptail --title "$title" --inputbox "$prompt" 12 78 "$default" 3>&1 1>&2 2>&3)" || exit 130
  else
    read -r -p "$prompt [$default]: " value
    value="${value:-$default}"
  fi
  printf '%s' "$value"
}

confirm() {
  local title="$1" body="$2"
  if [[ ${NON_INTERACTIVE} -eq 1 ]]; then return 0; fi
  if [[ "$UI" == whiptail ]]; then whiptail --title "$title" --yesno "$body" 20 78
  else read -r -p "$body [s/N]: " answer; [[ "$answer" =~ ^[sSyY]$ ]]; fi
}

valid_domain() { [[ "$1" =~ ^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$ ]]; }
valid_ipv4() {
  local ip="$1" octet
  [[ "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || return 1
  IFS=. read -r -a octets <<<"$ip"
  for octet in "${octets[@]}"; do
    [[ "$octet" =~ ^[0-9]+$ ]] && ((10#$octet <= 255)) || return 1
  done
}
valid_email() { [[ "$1" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; }

set_env() {
  local key="$1" value="$2" rendered temp
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || { echo "ERROR: valor inválido para $key" >&2; exit 1; }
  rendered="$value"
  if [[ "$value" =~ [[:space:]#] ]]; then
    rendered="${value//\\/\\\\}"
    rendered="${rendered//\"/\\\"}"
    rendered="\"${rendered}\""
  fi
  temp="$(mktemp)"
  awk -v key="$key" -v value="$rendered" '
    BEGIN { found=0 }
    $0 ~ "^" key "=" { print key "=" value; found=1; next }
    { print }
    END { if (!found) print key "=" value }
  ' "$ENV_FILE" >"$temp"
  install -m 0600 "$temp" "$ENV_FILE"
  rm -f "$temp"
}

detected_ip="$(curl -4fsS --max-time 5 https://api.ipify.org 2>/dev/null || true)"
base_domain="${SMARTDIAG_BASE_DOMAIN:-$(ask 'Dominio' 'Dominio base controlado por la empresa, sin https://' 'example.com')}"
server_ip="${SMARTDIAG_SERVER_IP:-$(ask 'Servidor' 'IPv4 pública de esta VPS' "${detected_ip:-127.0.0.1}")}"
acme_email="${SMARTDIAG_ACME_EMAIL:-$(ask 'TLS' 'Correo para certificados TLS/Let’s Encrypt' "admin@${base_domain}")}"
business_name="${SMARTDIAG_BUSINESS_NAME:-$(ask 'Empresa' 'Nombre comercial' 'SmartDiag504')}"
phone="${SMARTDIAG_PHONE:-$(ask 'Empresa' 'Teléfono con código de país' '+504 0000-0000')}"
address="${SMARTDIAG_ADDRESS:-$(ask 'Empresa' 'Dirección visible' 'Honduras')}"

valid_domain "$base_domain" || { echo "ERROR: dominio inválido: $base_domain" >&2; exit 1; }
valid_ipv4 "$server_ip" || { echo "ERROR: IPv4 inválida: $server_ip" >&2; exit 1; }
valid_email "$acme_email" || { echo "ERROR: correo inválido: $acme_email" >&2; exit 1; }

public_domain="taller.${base_domain}"
customer_domain="clientes.${base_domain}"
ops_domain="app.${base_domain}"
api_domain="api.${base_domain}"
erp_domain="erp.${base_domain}"

summary="IP: ${server_ip}
Landing/tienda: https://${public_domain}
Clientes: https://${customer_domain}
Operaciones: https://${ops_domain}
API: https://${api_domain}
ERPNext: https://${erp_domain}
Empresa: ${business_name}

Antes de continuar cree registros DNS A para los cinco nombres apuntando a ${server_ip}."
confirm "Confirmar instalación" "$summary" || exit 130

if [[ ! -f "$ENV_FILE" ]]; then install -m 0600 "${ROOT_DIR}/.env.example" "$ENV_FILE"; fi
set_env ENVIRONMENT production
set_env SEED_DEMO_DATA false
set_env ACME_EMAIL "$acme_email"
set_env PUBLIC_SITE_ADDRESS "$public_domain"
set_env CUSTOMER_SITE_ADDRESS "$customer_domain"
set_env OPS_SITE_ADDRESS "$ops_domain"
set_env API_SITE_ADDRESS "$api_domain"
set_env ERP_SITE_ADDRESS "$erp_domain"
set_env PUBLIC_DOMAIN "$public_domain"
set_env CUSTOMER_DOMAIN "$customer_domain"
set_env OPS_DOMAIN "$ops_domain"
set_env API_DOMAIN "$api_domain"
set_env ADMIN_DOMAIN "$erp_domain"
set_env FRAPPE_SITE_NAME "$erp_domain"
set_env ERP_SITE_NAME "$erp_domain"
set_env CORS_ORIGINS "https://${public_domain},https://${customer_domain},https://${ops_domain}"
set_env APPROVAL_PUBLIC_BASE_URL "https://${public_domain}"
set_env BUSINESS_NAME "$business_name"
set_env BUSINESS_PHONE "$phone"
set_env BUSINESS_EMAIL "info@${base_domain}"
set_env BUSINESS_ADDRESS "$address"
set_env OWNER_APPROVAL_EMAIL "$acme_email"
if [[ ${ENABLE_AI} -eq 1 ]]; then
  set_env LLM_PROVIDER ollama
  set_env CHROMA_ENABLED true
fi

if [[ ${DRY_RUN} -eq 0 ]]; then
  bootstrap=("${ROOT_DIR}/scripts/bootstrap-host.sh")
  [[ ${OPEN_FIREWALL} -eq 0 ]] || bootstrap+=(--open-firewall)
  "${bootstrap[@]}"
elif ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 es obligatorio para --dry-run; no se instalarán paquetes en ese modo." >&2
  exit 1
fi

"${ROOT_DIR}/scripts/generate-secrets.sh" "$ENV_FILE"
chmod 0600 "$ENV_FILE"

message "Configuración preparada" "$summary

El archivo privado quedó en ${ENV_FILE}. No lo suba a Git."

if [[ ${DRY_RUN} -eq 1 ]]; then
  grep -q '^SEED_DEMO_DATA=false$' "$ENV_FILE"
  grep -q '__GENERATE__' "$ENV_FILE" && { echo "ERROR: quedaron secretos sin generar" >&2; exit 1; }
  echo "DRY_RUN_OK domains=5 production=true seed_demo=false"
  exit 0
fi

install_args=(--env-file "$ENV_FILE")
[[ ${ENABLE_AI} -eq 0 ]] || install_args+=(--local-ai)
[[ ${ENABLE_OBSERVABILITY} -eq 0 ]] || install_args+=(--observability)
"${ROOT_DIR}/scripts/install-vps.sh" "${install_args[@]}"

message "Instalación terminada" "SmartDiag504 respondió a sus pruebas internas.

Operaciones: https://${ops_domain}
ERPNext: https://${erp_domain}
Landing: https://${public_domain}

Conserve ${ENV_FILE} y configure inmediatamente respaldo externo, SMTP, fiscalidad y hardware POS."
