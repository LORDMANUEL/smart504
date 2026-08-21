from __future__ import annotations


def test_heartbeats_and_leader_lease_fail_over(client, admin_headers):
    for node in ("node-a", "node-b"):
        response = client.post(
            "/api/v1/internal/heartbeat",
            headers=admin_headers,
            json={"node_id": node, "role": "application", "healthy": True, "details": {"version": "0.3.0"}},
        )
        assert response.status_code == 202

    status = client.get("/api/v1/ha/status", headers=admin_headers)
    assert status.status_code == 200
    assert {node["node_id"] for node in status.json()["nodes"]} == {"node-a", "node-b"}

    first = client.post(
        "/api/v1/ha/leader/acquire",
        headers=admin_headers,
        json={"lease_name": "alerts-worker", "node_id": "node-a", "ttl_seconds": 30},
    )
    assert first.status_code == 200
    assert first.json()["is_leader"] is True

    denied = client.post(
        "/api/v1/ha/leader/acquire",
        headers=admin_headers,
        json={"lease_name": "alerts-worker", "node_id": "node-b", "ttl_seconds": 30},
    )
    assert denied.status_code == 200
    assert denied.json()["is_leader"] is False
    assert denied.json()["leader_node_id"] == "node-a"
