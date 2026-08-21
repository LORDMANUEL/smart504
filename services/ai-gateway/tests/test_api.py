import os

from fastapi.testclient import TestClient

from smartdiag_ai_gateway.main import create_app


os.environ["AI_GATEWAY_INTERNAL_TOKEN"] = "test-ai-token"
client = TestClient(create_app(testing=True))


def test_assistant_requires_internal_token() -> None:
    response = client.post("/v1/assist", json={"question": "OT atrasadas", "role": "supervisor"})
    assert response.status_code == 401


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_assistant_blocks_sensitive_write_request() -> None:
    response = client.post("/v1/assist", headers={"X-AI-Gateway-Token": "test-ai-token"}, json={"question": "Registra el pago y entrega el carro", "role": "advisor"})
    assert response.status_code == 403


def test_assistant_answers_read_only_request_with_audit_id() -> None:
    response = client.post("/v1/assist", headers={"X-AI-Gateway-Token": "test-ai-token"}, json={"question": "Muéstrame las OT atrasadas", "role": "supervisor"})
    assert response.status_code == 200
    body = response.json()
    assert body["audit_id"]
    assert body["answer"]
    assert body["mode"] == "demo"
