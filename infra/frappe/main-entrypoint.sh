#!/usr/bin/env bash
set -euo pipefail
ASSETS_PATH=/home/frappe/frappe-bench/sites/assets
BAKED_PATH=/home/frappe/frappe-bench/assets
rm -rf "$ASSETS_PATH"
mkdir -p "$(dirname "$ASSETS_PATH")"
ln -s "$BAKED_PATH" "$ASSETS_PATH"
exec "$@"
