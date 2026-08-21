from __future__ import annotations

import base64
import os
import re
import shutil
from pathlib import Path

from playwright.sync_api import Page

ROOT = Path(__file__).resolve().parents[1]


def chromium_launch_options() -> dict[str, object]:
    options: dict[str, object] = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage", "--allow-file-access-from-files"],
    }
    executable = os.environ.get("CHROMIUM_PATH") or shutil.which("chromium") or shutil.which("chromium-browser")
    if executable:
        options["executable_path"] = executable
    return options


def load_app(page: Page, app_name: str, *, config: dict[str, object] | None = None) -> None:
    app_dir = ROOT / "apps" / app_name
    # These deterministic fixtures exercise the dependency-free interaction
    # contract with the legacy browser bundle. The production React surfaces
    # are compiled and tested by Vitest in CI/Docker where npm dependencies are
    # installed. Keeping the fixture under tests avoids shipping temporary HTML
    # beside production assets.
    html_path = ROOT / "tests" / "fixtures" / f"{app_name}-browser.html"
    html = html_path.read_text(encoding="utf-8")
    mark = (ROOT / "packages" / "design-system" / "assets" / "smartdiag504-mark.svg").read_bytes()
    mark_uri = "data:image/svg+xml;base64," + base64.b64encode(mark).decode("ascii")
    html = html.replace("../../packages/design-system/assets/smartdiag504-mark.svg", mark_uri)
    html = html.replace("<head>", f'<head><base href="{app_dir.as_uri()}/">', 1)
    html = re.sub(r"<link[^>]+rel=[\"']stylesheet[\"'][^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<script[^>]+src=[\"'][^\"']+[\"'][^>]*></script>", "", html, flags=re.IGNORECASE)
    page.set_content(html, wait_until="load")
    page.add_style_tag(path=str(ROOT / "packages" / "design-system" / "tokens.css"))
    page.add_style_tag(path=str(ROOT / "packages" / "design-system" / "components.css"))
    page.add_style_tag(path=str(app_dir / "styles.css"))
    if config is not None:
        page.evaluate("config => { window.SMARTDIAG_CONFIG = config; }", config)
    page.add_script_tag(path=str(app_dir / "app.js"))
