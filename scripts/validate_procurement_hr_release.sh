#!/usr/bin/env bash
set -Eeuo pipefail

repo_dir="${1:-/opt/smartdiag504-demo}"
erp_image="${SMARTDIAG_ERP_IMAGE:-smartdiag504-erpnext-workshop:36}"

docker run --rm \
  -v smartdiag-pip-cache:/root/.cache/pip \
  -v "$repo_dir:/workspace" \
  -w /workspace/services/platform-api \
  python:3.12-slim \
  sh -lc 'pip install -q /workspace/packages/smartdiag_domain -r requirements.txt pytest && PYTHONPATH=/workspace/services/platform-api python -m pytest -q'

docker build -t smartdiag504-ops-web:procurement-hr-20260817 "$repo_dir/apps/ops-web"

docker run --rm \
  -v "$repo_dir/frappe-apps/smartdiag_workshop/smartdiag_workshop/api/operations.py:/tmp/operations.py:ro" \
  "$erp_image" \
  python -m py_compile /tmp/operations.py

echo 'procurement-hr-release-gates-ok'
