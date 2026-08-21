FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates curl mariadb-client postgresql-client restic tar zstd coreutils findutils \
    && rm -rf /var/lib/apt/lists/*
COPY infra/backup/run-backup.sh /usr/local/bin/run-backup.sh
RUN chmod 755 /usr/local/bin/run-backup.sh
ENTRYPOINT ["/usr/local/bin/run-backup.sh"]
