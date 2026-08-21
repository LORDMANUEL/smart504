from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = {
    "apps/public-web",
    "apps/ops-web",
    "packages/design-system",
    "packages/smartdiag_domain",
    "services/platform-api",
    "services/ai-gateway",
    "services/alerts-worker",
    "frappe-apps/smartdiag_workshop",
    "infra/frappe",
    "infra/caddy",
    "infra/postgres/init",
    "contracts",
    "scripts",
}

REQUIRED_FILES = {
    "README.md",
    "AGENTS.md",
    ".env.example",
    "Makefile",
    "compose.yaml",
    "compose.preview.yaml",
    "contracts/events.yaml",
    "contracts/openapi-public.yaml",
}


def test_repository_has_required_directories() -> None:
    missing = sorted(path for path in REQUIRED_DIRS if not (ROOT / path).is_dir())
    assert not missing, f"Missing required directories: {missing}"


def test_repository_has_required_files() -> None:
    missing = sorted(path for path in REQUIRED_FILES if not (ROOT / path).is_file())
    assert not missing, f"Missing required files: {missing}"
