#!/usr/bin/env bash
set -euo pipefail
ENV_FILE=${1:-.env.ha}
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)
cd "$ROOT/infra/ha/two-node/witness"
docker compose --env-file "$ENV_FILE" -f compose.witness.yaml config --quiet
docker compose --env-file "$ENV_FILE" -f compose.witness.yaml up -d --build
