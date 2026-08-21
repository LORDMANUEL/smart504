#!/usr/bin/env python3
from __future__ import annotations

import base64
import os
import re
import shutil
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "previews"


def launch_options() -> dict[str, object]:
    options: dict[str, object] = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage", "--allow-file-access-from-files"],
    }
    executable = os.environ.get("CHROMIUM_PATH") or shutil.which("chromium") or shutil.which("chromium-browser")
    if executable:
        options["executable_path"] = executable
    return options


def load_app(page: Page, app_name: str) -> None:
    app_dir = ROOT / "apps" / app_name
    # The checked-in browser bundle is intentionally dependency-free. Its
    # matching deterministic HTML lives with the browser fixtures; the Vite
    # index only contains the React mount node and cannot host app.js directly.
    html = (ROOT / "tests" / "fixtures" / f"{app_name}-browser.html").read_text(encoding="utf-8")
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
    page.add_script_tag(path=str(app_dir / "app.js"))


def screenshot_surface(
    page: Page,
    app_name: str,
    output_name: str,
    *,
    click_selector: str | None = None,
    scroll_selector: str | None = None,
) -> None:
    load_app(page, app_name)
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_timeout(150)
    if click_selector:
        page.locator(click_selector).first.click()
        page.wait_for_timeout(150)
    if scroll_selector:
        page.evaluate(
            "selector => { const el = document.querySelector(selector); if (el) { window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 72); } }",
            scroll_selector,
        )
        page.wait_for_timeout(150)
    page.screenshot(path=str(OUTPUT / output_name), full_page=False)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_options())
        desktop = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1, locale="es-HN")
        screenshot_surface(desktop.new_page(), "public-web", "public-home-desktop.png")
        screenshot_surface(desktop.new_page(), "ops-web", "ops-dashboard-desktop.png")
        desktop.close()

        tablet = browser.new_context(viewport={"width": 1024, "height": 900}, device_scale_factor=1, locale="es-HN")
        screenshot_surface(
            tablet.new_page(),
            "ops-web",
            "ops-bays-tablet.png",
            click_selector="[data-view-target='workshop']",
        )
        tablet.close()

        mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, locale="es-HN")
        screenshot_surface(
            mobile.new_page(),
            "public-web",
            "public-store-mobile.png",
            scroll_selector="#repuestos",
        )
        mobile.close()
        browser.close()

    for path in sorted(OUTPUT.glob("*.png")):
        print(f"Captured {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
