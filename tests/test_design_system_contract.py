import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "packages" / "design-system" / "tokens.css"
COMPONENTS = ROOT / "packages" / "design-system" / "components.css"
BRAND = ROOT / "packages" / "design-system" / "brand.ts"
MARK = ROOT / "packages" / "design-system" / "assets" / "smartdiag504-mark.svg"

REQUIRED_TOKENS = {
    "--sd-navy-950",
    "--sd-navy-800",
    "--sd-blue-600",
    "--sd-cyan-500",
    "--sd-amber-500",
    "--sd-white",
    "--sd-slate-50",
    "--sd-slate-200",
    "--sd-ink",
    "--sd-muted",
    "--sd-success",
    "--sd-warning",
    "--sd-danger",
    "--sd-focus-ring",
    "--sd-radius-sm",
    "--sd-shadow-lg",
    "--sd-space-6",
}


def test_required_design_tokens_are_declared_once() -> None:
    content = TOKENS.read_text(encoding="utf-8")
    declared = set(re.findall(r"(--sd-[a-z0-9-]+)\s*:", content))
    assert REQUIRED_TOKENS <= declared
    for token in REQUIRED_TOKENS:
        assert content.count(f"{token}:") == 1, f"{token} must have one canonical value"


def test_components_include_accessible_interaction_states() -> None:
    content = COMPONENTS.read_text(encoding="utf-8")
    for selector in (".sd-button", ".sd-input", ".sd-status", ".sd-table", ".sd-shell"):
        assert selector in content
    assert ":focus-visible" in content
    assert "prefers-reduced-motion" in content
    assert "min-height: 44px" in content


def test_brand_contract_and_svg_are_present() -> None:
    brand = BRAND.read_text(encoding="utf-8")
    svg = MARK.read_text(encoding="utf-8")
    assert 'name: "SmartDiag504"' in brand
    assert 'tagline: "Diagnóstico preciso. Servicio transparente."' in brand
    assert 'aria-label="SmartDiag504"' in svg
    assert "<svg" in svg and "viewBox=" in svg
