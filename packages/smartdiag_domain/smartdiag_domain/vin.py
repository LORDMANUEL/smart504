from __future__ import annotations

import re

VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def normalize_vin(value: str) -> str:
    """Return an uppercase VIN without surrounding or embedded whitespace."""
    return "".join(value.upper().split())


def validate_vin(value: str) -> str:
    """Validate the ISO-style 17-character VIN structure.

    This validation deliberately does not enforce the North-American check digit,
    because imported vehicles can follow markets where that digit is not mandatory.
    """
    normalized = normalize_vin(value)
    if not VIN_PATTERN.fullmatch(normalized):
        raise ValueError("VIN must contain 17 characters and cannot include I, O or Q")
    return normalized
