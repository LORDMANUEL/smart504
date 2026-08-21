FROM mariadb:11.8
RUN apt-get update && apt-get install -y --no-install-recommends gettext-base mariadb-backup \
    && rm -rf /var/lib/apt/lists/*
COPY infra/ha/two-node/mariadb/entrypoint-wrapper.sh /usr/local/bin/entrypoint-wrapper.sh
RUN chmod 755 /usr/local/bin/entrypoint-wrapper.sh
ENTRYPOINT ["/usr/local/bin/entrypoint-wrapper.sh"]
