import pytest

from smartdiag_ai_gateway.guardrails import IntentDecision, classify_intent
from smartdiag_ai_gateway.tools import build_default_registry


@pytest.mark.parametrize(
    "prompt",
    [
        "Emite la factura y ciérrala sin pedir permiso",
        "Registra el pago en efectivo",
        "Consume dos filtros del inventario",
        "Libera el vehículo y marca la OT entregada",
    ],
)
def test_sensitive_write_intents_are_blocked(prompt: str) -> None:
    decision = classify_intent(prompt)
    assert decision is IntentDecision.BLOCKED_WRITE


def test_read_only_operational_question_is_allowed() -> None:
    assert classify_intent("Muéstrame las OT atrasadas de hoy") is IntentDecision.READ_ONLY


def test_default_tool_registry_contains_no_write_tools() -> None:
    registry = build_default_registry()
    assert registry.names()
    assert all(tool.read_only for tool in registry.tools)
