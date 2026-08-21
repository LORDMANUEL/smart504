from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_installer_delegates_to_guided_installer() -> None:
    installer = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert "scripts/install-gui.sh" in installer


def test_guided_installer_enforces_production_without_demo_seed() -> None:
    installer = (ROOT / "scripts" / "install-gui.sh").read_text(encoding="utf-8")
    assert "set_env ENVIRONMENT production" in installer
    assert "set_env SEED_DEMO_DATA false" in installer
    assert "DRY_RUN_OK domains=5 production=true seed_demo=false" in installer


def test_guided_installer_configures_all_public_surfaces() -> None:
    installer = (ROOT / "scripts" / "install-gui.sh").read_text(encoding="utf-8")
    for prefix in ("taller", "clientes", "app", "api", "erp"):
        assert f'{prefix}.${{base_domain}}' in installer


def test_private_runtime_files_are_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", "secrets/*", "*.sqlite", "artifacts/"):
        assert pattern in gitignore
