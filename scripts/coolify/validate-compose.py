#!/usr/bin/env python3
"""Validate Coolify Compose while accounting for Coolify-only service keys."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "compose.coolify.yaml"


def main() -> int:
    document = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    for service in document.get("services", {}).values():
        service.pop("exclude_from_hc", None)
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", encoding="utf-8", delete=False) as handle:
        yaml.safe_dump(document, handle, sort_keys=False)
        temporary = Path(handle.name)
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(temporary), "config", "--quiet"],
            cwd=ROOT,
            env=os.environ,
            check=False,
        )
        return result.returncode
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
