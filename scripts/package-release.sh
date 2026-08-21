#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION=${SMARTDIAG_VERSION:-0.4.0}
OUT=${1:-/mnt/data/smartdiag504_platform_complete_v${VERSION}.zip}
DOC_OUT=${2:-/mnt/data/SMARTDIAG504_IMPLEMENTATION_MASTER_V0.4.md}
REPORT_OUT=${3:-/mnt/data/SMARTDIAG504_VERIFICATION_REPORT_V0.4.md}
MANIFEST_OUT=${4:-/mnt/data/SMARTDIAG504_MANIFEST_V0.4.sha256}
cd "${ROOT}"

./scripts/verify.sh
manifest_tmp="$(mktemp)"
trap 'rm -f "${manifest_tmp}"' EXIT
find . -type f \
  ! -path './.git/*' \
  ! -path '*/node_modules/*' \
  ! -path '*/dist/*' \
  ! -path '*/.pytest_cache/*' \
  ! -path '*/.ruff_cache/*' \
  ! -path '*/__pycache__/*' \
  ! -path '*/*.egg-info/*' \
  ! -path '*/backups/*' \
  ! -name '*.pyc' \
  ! -name '.env' \
  ! -name '.env.local' \
  ! -name 'MANIFEST.sha256' \
  ! -name 'browser-test.html' \
  -print0 | sort -z | xargs -0 sha256sum >"${manifest_tmp}"
mv "${manifest_tmp}" MANIFEST.sha256
trap - EXIT

rm -f "${OUT}" "${OUT}.sha256"
python3 - "${ROOT}" "${OUT}" "${VERSION}" <<'PY'
from pathlib import Path
import sys
import zipfile

root = Path(sys.argv[1])
out = Path(sys.argv[2])
version = sys.argv[3]
exclude_parts = {'.git', 'node_modules', 'dist', '.pytest_cache', '.ruff_cache', '__pycache__', 'backups'}
exclude_names = {'.env', '.env.local', 'browser-test.html'}
prefix = Path(f'smartdiag504-platform-v{version}')
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if any(part in exclude_parts or part.endswith('.egg-info') for part in path.parts):
            continue
        if path.name in exclude_names or path.suffix == '.pyc':
            continue
        archive.write(path, prefix / path.relative_to(root))
PY

archive_hash=$(sha256sum "${OUT}" | awk '{print $1}')
printf '%s  %s\n' "${archive_hash}" "$(basename "${OUT}")" > "${OUT}.sha256"
unzip -t "${OUT}" >/dev/null
cp SMARTDIAG504_IMPLEMENTATION_MASTER.md "${DOC_OUT}"
cp docs/testing/VERIFICATION_REPORT.md "${REPORT_OUT}"
cp MANIFEST.sha256 "${MANIFEST_OUT}"
printf 'Release: %s\nSHA256: %s\nMaster: %s\nVerification: %s\n' \
  "${OUT}" "${archive_hash}" "${DOC_OUT}" "${REPORT_OUT}"
