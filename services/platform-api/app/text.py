from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Create a stable ASCII slug without an optional runtime dependency."""
    normalized = (
        unicodedata.normalize("NFKD", value.strip()).encode("ascii", "ignore").decode("ascii")
    )
    slug = _NON_ALNUM.sub("-", normalized.casefold()).strip("-")
    return slug or "item"
