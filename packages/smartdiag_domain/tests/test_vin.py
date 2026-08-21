import pytest

from smartdiag_domain.vin import normalize_vin, validate_vin


def test_normalize_vin_removes_spaces_and_uppercases() -> None:
    assert normalize_vin(" 1fm5k8gc2lgc12345 ") == "1FM5K8GC2LGC12345"


def test_validate_vin_accepts_valid_structure() -> None:
    assert validate_vin("1FM5K8GC2LGC12345") == "1FM5K8GC2LGC12345"


@pytest.mark.parametrize("vin", ["", "ABC", "1FM5K8GCO LGC12345", "1FM5K8GCI1GC12345"])
def test_validate_vin_rejects_invalid_values(vin: str) -> None:
    with pytest.raises(ValueError):
        validate_vin(vin)
