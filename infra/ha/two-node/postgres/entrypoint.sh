#!/usr/bin/env bash
set -euo pipefail
: "${NODE_NAME:?NODE_NAME required}"
: "${NODE_PRIVATE_IP:?NODE_PRIVATE_IP required}"
: "${PATRONI_SCOPE:?PATRONI_SCOPE required}"
: "${ETCD_HOSTS:?ETCD_HOSTS required}"
: "${POSTGRES_SUPERUSER_PASSWORD:?POSTGRES_SUPERUSER_PASSWORD required}"
: "${POSTGRES_REPLICATION_PASSWORD:?POSTGRES_REPLICATION_PASSWORD required}"
envsubst < /templates/patroni.yml.template > /tmp/patroni.yml
exec patroni /tmp/patroni.yml
