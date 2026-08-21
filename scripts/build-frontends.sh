#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
REQUIRE_DEPS=0
RUN_TESTS=1
USE_INSTALLED_DEPS=1
if grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  # A Windows node_modules tree contains Windows-native Rollup binaries and
  # cannot be executed by Linux Node inside WSL. Use the portable syntax gate;
  # native Windows and Docker/CI still run the dependency-based builds.
  USE_INSTALLED_DEPS=0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) shift ;;
    --require-deps) REQUIRE_DEPS=1; shift ;;
    --no-tests) RUN_TESTS=0; shift ;;
    -h|--help)
      echo "Usage: $0 [--check] [--require-deps] [--no-tests]"
      exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; exit 2 ;;
  esac
done

smartdiag_typescript_syntax_check() {
  local npm_root
  command -v node >/dev/null 2>&1 || { echo "ERROR: Node.js is required." >&2; exit 1; }
  command -v npm >/dev/null 2>&1 || { echo "ERROR: npm is required." >&2; exit 1; }
  npm_root=$(npm root -g)
  if [[ ! -d "${npm_root}/typescript" && -d "apps/public-web/node_modules/typescript" ]]; then
    npm_root="${ROOT_DIR}/apps/public-web/node_modules"
  fi
  [[ -d "${npm_root}/typescript" ]] || {
    echo "ERROR: TypeScript 5.8.3 is required globally when frontend dependencies are absent." >&2
    exit 1
  }
  node - "${npm_root}" <<'NODE'
const fs = require('fs');
const path = require('path');
const ts = require(process.argv[2] + '/typescript');
const roots = ['apps/public-web/src', 'apps/ops-web/src'];
const files = [];
for (const root of roots) {
  const walk = (directory) => {
    for (const entry of fs.readdirSync(directory, {withFileTypes: true})) {
      const value = path.join(directory, entry.name);
      if (entry.isDirectory()) walk(value);
      else if (/\.(ts|tsx)$/.test(entry.name) && !entry.name.endsWith('.d.ts')) files.push(value);
    }
  };
  walk(root);
}
let failed = false;
for (const file of files) {
  const source = fs.readFileSync(file, 'utf8');
  const result = ts.transpileModule(source, {
    fileName: file,
    reportDiagnostics: true,
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ESNext,
      jsx: ts.JsxEmit.ReactJSX,
      isolatedModules: true,
    },
  });
  for (const diagnostic of result.diagnostics || []) {
    if (diagnostic.category !== ts.DiagnosticCategory.Error) continue;
    failed = true;
    console.error(`${file}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`);
  }
}
if (failed) process.exit(1);
console.log(`TypeScript/TSX syntax passed for ${files.length} source files.`);
NODE
}

full_builds=0
for app in apps/public-web apps/ops-web; do
  if [[ ${USE_INSTALLED_DEPS} -eq 1 && -x "${app}/node_modules/.bin/vite" && -x "${app}/node_modules/.bin/vitest" ]]; then
    if [[ ${RUN_TESTS} -eq 1 ]]; then
      npm --prefix "${app}" test
    fi
    npm --prefix "${app}" run build
    full_builds=$((full_builds + 1))
  elif [[ ${REQUIRE_DEPS} -eq 1 ]]; then
    echo "ERROR: ${app}/node_modules is missing. Run npm install in both frontend applications." >&2
    exit 1
  fi
done

if [[ ${full_builds} -lt 2 ]]; then
  smartdiag_typescript_syntax_check
  echo "Frontend dependency-based tests/builds were not run locally because node_modules is absent. Docker/CI installs the pinned packages and runs the full builds."
else
  echo "Both React frontends passed unit tests and production builds."
fi
