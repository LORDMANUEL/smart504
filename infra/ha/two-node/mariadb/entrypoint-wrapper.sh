#!/usr/bin/env bash
set -euo pipefail
: "${GALERA_SST_PASSWORD:?GALERA_SST_PASSWORD required}"
envsubst < /templates/galera.cnf.template > /etc/mysql/conf.d/90-smartdiag-galera.cnf
mkdir -p /docker-entrypoint-initdb.d
cat > /docker-entrypoint-initdb.d/10-smartdiag-sst-user.sql <<SQL
CREATE USER IF NOT EXISTS 'sstuser'@'%' IDENTIFIED BY '${GALERA_SST_PASSWORD}';
GRANT RELOAD, LOCK TABLES, PROCESS, REPLICATION CLIENT ON *.* TO 'sstuser'@'%';
FLUSH PRIVILEGES;
SQL
if [ "${GALERA_BOOTSTRAP:-0}" = "1" ]; then
  exec docker-entrypoint.sh mariadbd --wsrep-new-cluster
fi
exec docker-entrypoint.sh mariadbd
