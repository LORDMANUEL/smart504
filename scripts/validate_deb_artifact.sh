#!/usr/bin/env bash
set -Eeuo pipefail

artifact="${1:-/opt/smartdiag504-demo/artifacts/debian/smartdiag504-platform_0.4.0_all.deb}"
test -s "$artifact"
docker run --rm -v "$artifact:/package.deb:ro" debian:bookworm-slim bash -lc '
  set -eu
  mkdir -p /tmp/package
  dpkg-deb -x /package.deb /tmp/package
  dpkg-deb -e /package.deb /tmp/control
  /tmp/package/usr/bin/smartdiag504 version
  test -r /tmp/package/usr/lib/smartdiag504/source/compose.yaml
  test -r /tmp/package/usr/share/smartdiag504/platform.env.example
  test -x /tmp/package/usr/bin/smartdiag504
  ! grep -Eq "docker compose .*up|systemctl .*enable" /tmp/control/postinst
  echo deb-artifact-safe-ok
'
(cd "$(dirname "$artifact")" && sha256sum -c "$(basename "$artifact").sha256")
