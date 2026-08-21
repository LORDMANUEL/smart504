FROM postgres:17-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip curl jq gettext-base \
    && pip3 install --break-system-packages "patroni[etcd3]==4.0.6" "psycopg[binary]==3.2.9" \
    && rm -rf /var/lib/apt/lists/*
COPY infra/ha/two-node/postgres/entrypoint.sh /usr/local/bin/patroni-entrypoint.sh
RUN chmod 755 /usr/local/bin/patroni-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/patroni-entrypoint.sh"]
