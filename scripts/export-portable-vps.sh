#!/usr/bin/env bash
set -Eeuo pipefail

# Exporta una entrega portable sin copiar secretos del VPS origen.
# Debe ejecutarse como root en el VPS de pruebas porque lee volúmenes Docker.
SOURCE_DIR=${SMARTDIAG_SOURCE_DIR:-/opt/smartdiag504-demo}
ERP_SOURCE_DIR=${SMARTDIAG_ERP_SOURCE_DIR:-/opt/smartdiag504-erpnext}
OUTPUT_DIR=${1:-/opt/smartdiag504-portable}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
WORK_DIR="${OUTPUT_DIR}/smartdiag504-portable-${STAMP}"
ARCHIVE="${OUTPUT_DIR}/smartdiag504-portable-${STAMP}.tar.zst"

[[ $(id -u) -eq 0 ]] || { echo "ERROR: ejecutar como root" >&2; exit 2; }
[[ -d "${SOURCE_DIR}" ]] || { echo "ERROR: no existe ${SOURCE_DIR}" >&2; exit 2; }
command -v docker >/dev/null
command -v tar >/dev/null
command -v zstd >/dev/null
mkdir -p "${WORK_DIR}/source" "${WORK_DIR}/data/platform" "${WORK_DIR}/data/erpnext/source" "${WORK_DIR}/data/erpnext/backups" "${WORK_DIR}/metadata"

# Código reproducible: nunca transportar .env, claves, logs o paquetes históricos.
tar -C "${SOURCE_DIR}" -cf - \
  --exclude=.env --exclude='*.env' --exclude=secrets --exclude=.git --exclude=.venv --exclude=node_modules --exclude=dist \
  --exclude=backups --exclude='*.log' --exclude='*.err' --exclude='*.tar' \
  --exclude='*.tar.gz' --exclude='*.zip' --exclude='.pytest_cache' \
  . | tar -C "${WORK_DIR}/source" -xf -

if [[ -d "${ERP_SOURCE_DIR}" ]]; then
  tar -C "${ERP_SOURCE_DIR}" -cf - --exclude=.env --exclude=.git --exclude='*.log' \
    --exclude='compose.generated.yml*' --exclude='*.bak-*' --exclude='*.pre*' . \
    | tar -C "${WORK_DIR}/data/erpnext/source" --no-same-owner -xf -
fi

POSTGRES_CONTAINER=${POSTGRES_CONTAINER:-postgres-eeylxzuvyicq5i5lelcrcda9}
docker exec "${POSTGRES_CONTAINER}" sh -lc \
  'exec pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > "${WORK_DIR}/data/platform/platform-demo.pgdump"

archive_volume() {
  local volume=$1 output=$2
  docker volume inspect "${volume}" >/dev/null
  docker run --rm -v "${volume}:/source:ro" -v "${WORK_DIR}/data/platform:/export" alpine:3.22 \
    sh -lc "tar -C /source -czf /export/${output} ."
}
archive_volume eeylxzuvyicq5i5lelcrcda9_platform-media platform-media.tar.gz
archive_volume eeylxzuvyicq5i5lelcrcda9_chroma-data chroma-data.tar.gz
archive_volume eeylxzuvyicq5i5lelcrcda9_ollama-data ollama-data.tar.gz
archive_volume eeylxzuvyicq5i5lelcrcda9_redis-data valkey-data.tar.gz

# Exportar objetos S3 sin transportar claves ni la configuración RPC de Garage.
# El destino crea credenciales nuevas y reimporta estos objetos al bucket privado.
GARAGE_SECRET_FILE=${GARAGE_SECRET_FILE:-${SOURCE_DIR}/secrets/s3.env}
GARAGE_NETWORK=${GARAGE_NETWORK:-eeylxzuvyicq5i5lelcrcda9}
PLATFORM_API_IMAGE=${PLATFORM_API_IMAGE:-smartdiag504-demo-platform-api:latest}
[[ -s "${GARAGE_SECRET_FILE}" ]] || { echo "ERROR: falta configuración S3 privada" >&2; exit 2; }
mkdir -p "${WORK_DIR}/data/platform/garage-objects"
chown 10001:10001 "${WORK_DIR}/data/platform/garage-objects"
docker run --rm --network "${GARAGE_NETWORK}" --env-file "${GARAGE_SECRET_FILE}" \
  -e S3_ENDPOINT_URL=http://garage:3900 \
  -v "${WORK_DIR}/data/platform/garage-objects:/export" \
  "${PLATFORM_API_IMAGE}" python -c '
import os
from pathlib import Path, PurePosixPath
import boto3

root = Path("/export")
client = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT_URL"],
    region_name=os.environ["S3_REGION"],
    aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
)
bucket = os.environ["S3_BUCKET"]
paginator = client.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=bucket):
    for item in page.get("Contents", []):
        key = PurePosixPath(item["Key"])
        if key.is_absolute() or ".." in key.parts:
            raise RuntimeError("unsafe S3 object key")
        destination = root.joinpath(*key.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, item["Key"], str(destination))
'
tar -C "${WORK_DIR}/data/platform/garage-objects" -czf \
  "${WORK_DIR}/data/platform/garage-objects.tar.gz" .
rm -rf "${WORK_DIR}/data/platform/garage-objects"

ERP_BACKEND=${ERP_BACKEND:-smartdiag504-erp-backend-1}
ERP_SITE=${ERP_SITE:-erp.nexusmedi.org}
docker exec "${ERP_BACKEND}" bench --site "${ERP_SITE}" backup --with-files --compress >/dev/null
docker cp "${ERP_BACKEND}:/home/frappe/frappe-bench/sites/${ERP_SITE}/private/backups/." \
  "${WORK_DIR}/data/erpnext/backups/"
# La configuración del sitio contiene credenciales del VPS origen. La nueva
# instalación crea su propio site_config y restaura únicamente DB + archivos.
find "${WORK_DIR}/data/erpnext/backups" -type f -name '*site_config_backup.json' -delete

cat > "${WORK_DIR}/metadata/export.json" <<JSON
{
  "product": "SmartDiag504",
  "version": "0.4.0",
  "created_at_utc": "${STAMP}",
  "source_vps_role": "TEST_ONLY",
  "contains_secrets": false,
  "platform_database": "PostgreSQL custom dump",
  "erp_database": "Frappe bench backup with files",
  "restore_policy": "RESTORE_ONLY_IN_EMPTY_STAGING_FIRST",
  "private_object_storage": "Garage objects without source credentials"
}
JSON

cp "${SOURCE_DIR}/.env.example" "${WORK_DIR}/metadata/platform.env.example"
(cd "${WORK_DIR}" && find . -type f ! -name manifest.sha256 -print0 | sort -z | xargs -0 sha256sum > manifest.sha256)
(cd "${WORK_DIR}" && sha256sum --check manifest.sha256 >/dev/null)
tar --zstd -C "${OUTPUT_DIR}" -cf "${ARCHIVE}" "$(basename "${WORK_DIR}")"
sha256sum "${ARCHIVE}" > "${ARCHIVE}.sha256"
tar --zstd -tf "${ARCHIVE}" >/dev/null

printf 'PORTABLE_ARCHIVE=%s\nSHA256_FILE=%s\nSTAGING_DIRECTORY=%s\n' "${ARCHIVE}" "${ARCHIVE}.sha256" "${WORK_DIR}"
