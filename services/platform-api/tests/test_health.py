def test_health_and_ready_do_not_expose_secrets(client) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    ready = client.get("/ready")
    assert ready.status_code == 200
    payload = ready.json()
    assert payload["checks"] == {"database": "ok", "security": "ok"}
    assert "test-admin-token" not in ready.text
    assert "test-heartbeat-token" not in ready.text


def test_live_and_startup_are_separate_from_readiness(client) -> None:
    assert client.get("/live").json()["status"] == "live"
    assert client.get("/startup").json()["status"] == "started"
