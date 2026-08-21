from datetime import datetime, timezone


def test_kanban_is_default_and_bays_are_optional(client, admin_headers) -> None:
    initial = client.get(
        "/api/v1/operations/settings/workshop", headers=admin_headers
    )
    assert initial.status_code == 200
    assert initial.json()["default_view"] == "KANBAN"
    assert initial.json()["bays_enabled"] is False

    enabled = client.put(
        "/api/v1/operations/settings/workshop",
        headers=admin_headers,
        json={
            "default_view": "BAYS",
            "bays_enabled": True,
            "bay_codes": ["B-01", "B-02"],
        },
    )
    assert enabled.status_code == 200
    assert enabled.json()["default_view"] == "BAYS"


def test_heartbeat_and_leader_fencing(client, heartbeat_headers, admin_headers) -> None:
    first = client.post(
        "/api/v1/cluster/heartbeats",
        headers=heartbeat_headers,
        json={
            "node_id": "node-a",
            "role": "platform-api",
            "status": "HEALTHY",
            "version": "0.3.0",
            "metadata": {"zone": "sps-a"},
        },
    )
    assert first.status_code == 200

    nodes = client.get("/api/v1/cluster/heartbeats", headers=admin_headers)
    assert any(item["node_id"] == "node-a" for item in nodes.json())

    lease_a = client.post(
        "/api/v1/cluster/leases/alerts-worker",
        headers=heartbeat_headers,
        json={"node_id": "node-a", "ttl_seconds": 60},
    )
    assert lease_a.status_code == 200
    assert lease_a.json()["fencing_token"] == 1

    lease_b = client.post(
        "/api/v1/cluster/leases/alerts-worker",
        headers=heartbeat_headers,
        json={"node_id": "node-b", "ttl_seconds": 60},
    )
    assert lease_b.status_code == 409
