from app.demo_data import PRELOADED_PARTS, VEHICLE_CATALOG


def test_vehicle_catalog_has_broad_demo_coverage() -> None:
    assert len({vehicle["make"] for vehicle in VEHICLE_CATALOG}) >= 12
    assert len(VEHICLE_CATALOG) >= 30
    assert len(PRELOADED_PARTS) == len(VEHICLE_CATALOG) * 3
    assert len({part["code"] for part in PRELOADED_PARTS}) == len(PRELOADED_PARTS)
    assert all(part["stock"] == 0 for part in PRELOADED_PARTS)
    assert all(part["requires_vin_validation"] for part in PRELOADED_PARTS)
