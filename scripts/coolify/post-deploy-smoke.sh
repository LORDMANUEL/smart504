#!/usr/bin/env bash
set -Eeuo pipefail

base_url="${1:?Usage: post-deploy-smoke.sh https://taller.example.org}"
base_url="${base_url%/}"

curl -fsS "${base_url}/" >/dev/null
curl -fsS "${base_url}/api/live" | grep -q '"status":"live"'
curl -fsS "${base_url}/api/startup" | grep -q '"status":"started"'
curl -fsS "${base_url}/api/ready" | grep -q '"status":"ready"'
echo "External infrastructure smoke passed for ${base_url}. Functional QA remains required."
