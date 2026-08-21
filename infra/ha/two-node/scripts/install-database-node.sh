#!/usr/bin/env bash
set -euo pipefail
ENV_FILE=${1:-.env.ha}
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)
cd "$ROOT/infra/ha/two-node"
docker compose --env-file "$ENV_FILE" -f postgres/compose.postgres-node.yaml config --quiet
docker compose --env-file "$ENV_FILE" -f mariadb/compose.mariadb-node.yaml config --quiet
docker compose --env-file "$ENV_FILE" -f postgres/compose.postgres-node.yaml up -d --build
docker compose --env-file "$ENV_FILE" -f mariadb/compose.mariadb-node.yaml up -d --build
