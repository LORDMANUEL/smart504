#!/usr/bin/env bash
set -Eeuo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="${SMARTDIAG_DEB_VERSION:-0.4.0}"
stage="$(mktemp -d)"
package_root="$stage/smartdiag504-platform_${version}_all"
output_dir="$repo_dir/artifacts/debian"
trap 'rm -rf "$stage"' EXIT

command -v dpkg-deb >/dev/null 2>&1 || { echo 'dpkg-deb no está disponible.' >&2; exit 1; }
install -d "$package_root/DEBIAN" "$package_root/usr/bin" "$package_root/usr/lib/smartdiag504/source" "$package_root/usr/share/smartdiag504"
sed "s/^Version:.*/Version: $version/" "$repo_dir/packaging/debian/control" > "$package_root/DEBIAN/control"
install -m 0755 "$repo_dir/packaging/debian/postinst" "$package_root/DEBIAN/postinst"
install -m 0755 "$repo_dir/packaging/debian/smartdiag504-cli" "$package_root/usr/bin/smartdiag504"
install -m 0644 "$repo_dir/packaging/debian/platform.env.example" "$package_root/usr/share/smartdiag504/platform.env.example"

tar -C "$repo_dir" \
  --exclude=.git --exclude=.venv --exclude=node_modules --exclude=artifacts --exclude=.pytest_cache --exclude=.ruff_cache \
  -cf - apps services packages frappe-apps infra scripts contracts docs compose.yaml compose.coolify.yaml pyproject.toml pytest.ini README.md ARCHITECTURE.md AGENTS.md \
  | tar -C "$package_root/usr/lib/smartdiag504/source" -xf -

install -d "$output_dir"
dpkg-deb --root-owner-group --build "$package_root" "$output_dir/smartdiag504-platform_${version}_all.deb"
dpkg-deb --info "$output_dir/smartdiag504-platform_${version}_all.deb"
(cd "$output_dir" && sha256sum "smartdiag504-platform_${version}_all.deb" > "smartdiag504-platform_${version}_all.deb.sha256")
