def test_operational_flow_is_persisted_and_aggregated(client, admin_headers) -> None:
    payload = {
        "module": "WAREHOUSE",
        "action": "PART_DELIVERED",
        "item_reference": "ESC-FIL-2020",
        "actor": "test-user",
        "result": "SUCCESS",
        "metadata": {"work_order": "OT-TEST-001", "location": "A-01-02"},
    }

    created = client.post("/api/v1/operations/flow-events", headers=admin_headers, json=payload)
    assert created.status_code == 201
    assert created.json()["metadata_json"]["work_order"] == "OT-TEST-001"

    heatmap = client.get("/api/v1/operations/flow-events/heatmap", headers=admin_headers)
    assert heatmap.status_code == 200
    warehouse_cells = [cell for cell in heatmap.json() if cell["module"] == "WAREHOUSE"]
    assert warehouse_cells == [
        {
            "module": "WAREHOUSE",
            "action": "PART_DELIVERED",
            "count": 1,
            "last_seen_at": created.json()["created_at"],
        }
    ]


def test_flow_events_require_admin(client) -> None:
    response = client.get("/api/v1/operations/flow-events/heatmap")
    assert response.status_code == 401
