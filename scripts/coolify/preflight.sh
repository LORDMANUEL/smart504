#!/usr/bin/env bash
set -Eeuo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${root_dir}"

[[ -f compose.coolify.yaml ]] || { echo "ERROR: compose.coolify.yaml is missing" >&2; exit 1; }
python3 scripts/coolify/validate-compose.py
python3 -m pytest -q tests/test_coolify_compose.py
echo "Coolify preflight passed. No host or Docker resources were changed."
