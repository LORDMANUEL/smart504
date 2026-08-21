#!/usr/bin/env bash
set -euo pipefail

threads="${GUNICORN_THREADS:-4}"
workers="${GUNICORN_WORKERS:-2}"
timeout="${GUNICORN_TIMEOUT:-120}"

exec /home/frappe/frappe-bench/env/bin/gunicorn \
  --chdir=/home/frappe/frappe-bench/sites \
  --bind=0.0.0.0:8000 \
  --threads="${threads}" \
  --workers="${workers}" \
  --worker-class=gthread \
  --worker-tmp-dir=/dev/shm \
  --timeout="${timeout}" \
  --preload \
  frappe.app:application
