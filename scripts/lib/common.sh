#!/usr/bin/env bash
set -Eeuo pipefail

smartdiag_url() {
  local value=${1:-}
  if [[ -z "${value}" ]]; then
    printf '%s\n' ""
  elif [[ "${value}" == http://* || "${value}" == https://* ]]; then
    printf '%s\n' "${value%/}"
  else
    printf 'https://%s\n' "${value%/}"
  fi
}

smartdiag_require_env_file() {
  local file=$1
  [[ -f "${file}" ]] || { echo "ERROR: environment file does not exist: ${file}" >&2; return 1; }
}

smartdiag_require_command() {
  local command_name=$1
  command -v "${command_name}" >/dev/null 2>&1 || {
    echo "ERROR: required command is not installed: ${command_name}" >&2
    return 1
  }
}
