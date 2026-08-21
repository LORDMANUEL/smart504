from datetime import date, timedelta

def test_authenticated_calendar_booking_is_separate_from_public_lead(client, client_account) -> None:
    login = client.post("/api/v1/client-auth/login", data={"username": client_account["email"], "password": client_account["password"]})
    assert login.status_code == 204
    tomorrow = date.today() + timedelta(days=2)
    available = client.get(
        "/api/v1/client-appointments/availability",
        params={"date": tomorrow.isoformat()},
    )
    assert available.status_code == 200
    slot = next(item for item in available.json()["slots"] if item["available"])

    created = client.post(
        "/api/v1/client-appointments",
        json={
            "vehicle_id": client_account["vehicle"].id,
            "vehicle_summary": "Ford Escape 2020",
            "service_requested": "Diagnóstico electrónico",
            "scheduled_at": slot["starts_at"],
            "concern": "Luz de motor encendida durante la aceleración.",
        },
    )
    assert created.status_code == 201
    assert created.json()["source"] == "CLIENT_PORTAL"
    assert created.json()["status"] == "CONFIRMED"

    listed = client.get("/api/v1/client-appointments")
    assert listed.status_code == 200
    assert listed.json()[0]["vehicle_id"] == client_account["vehicle"].id

    no_longer_available = client.get(
        "/api/v1/client-appointments/availability",
        params={"date": tomorrow.isoformat()},
    ).json()
    assert not next(
        item for item in no_longer_available["slots"] if item["starts_at"] == slot["starts_at"]
    )["available"]
