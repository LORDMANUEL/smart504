from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True, slots=True)
class Alert:
    code: str
    severity: str
    aggregate_id: str
    title: str
    message: str
    detected_at: datetime
    payload: dict[str, Any]


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class AlertRuleEngine:
    def evaluate(self, event: dict[str, Any], now: datetime | None = None) -> list[Alert]:
        detected_at = (now or datetime.now(UTC)).astimezone(UTC)
        event_type = str(event.get("event_type", "")).upper()
        aggregate_id = str(event.get("aggregate_id", "UNKNOWN"))
        payload = dict(event.get("payload") or {})
        alerts: list[Alert] = []

        if event_type == "WORK_ORDER_SNAPSHOT":
            status = str(payload.get("status", "")).upper()
            promised_at = _timestamp(payload.get("promised_at"))
            if promised_at and promised_at < detected_at and status not in {"DELIVERED", "CANCELLED"}:
                alerts.append(
                    Alert(
                        code="WORK_ORDER_OVERDUE",
                        severity="critical",
                        aggregate_id=aggregate_id,
                        title="OT fuera de fecha prometida",
                        message=f"La orden {aggregate_id} continúa en {status or 'estado desconocido'}.",
                        detected_at=detected_at,
                        payload=payload,
                    )
                )

        if event_type == "QUOTE_SNAPSHOT":
            status = str(payload.get("status", "")).upper()
            sent_at = _timestamp(payload.get("sent_at"))
            if status == "SENT" and sent_at and (detected_at - sent_at).total_seconds() > 48 * 3600:
                alerts.append(
                    Alert(
                        code="QUOTE_UNANSWERED",
                        severity="warning",
                        aggregate_id=aggregate_id,
                        title="Cotización sin respuesta",
                        message=f"La cotización {aggregate_id} supera 48 horas sin decisión del cliente.",
                        detected_at=detected_at,
                        payload=payload,
                    )
                )

        if event_type == "PART_REQUEST_SNAPSHOT":
            status = str(payload.get("status", "")).upper()
            requested_at = _timestamp(payload.get("requested_at"))
            if status in {"PENDING", "PARTIAL"} and requested_at:
                hours = (detected_at - requested_at).total_seconds() / 3600
                if hours > 2:
                    alerts.append(
                        Alert(
                            code="PART_REQUEST_DELAYED",
                            severity="critical" if hours > 8 else "warning",
                            aggregate_id=aggregate_id,
                            title="Solicitud de repuesto demorada",
                            message=f"La solicitud {aggregate_id} lleva {hours:.1f} horas pendiente.",
                            detected_at=detected_at,
                            payload=payload,
                        )
                    )

        if event_type == "TECHNICIAN_SNAPSHOT":
            status = str(payload.get("status", "")).upper()
            idle_since = _timestamp(payload.get("idle_since"))
            if status == "IDLE" and idle_since and (detected_at - idle_since).total_seconds() > 3600:
                minutes = int((detected_at - idle_since).total_seconds() / 60)
                alerts.append(
                    Alert(
                        code="TECHNICIAN_IDLE",
                        severity="warning",
                        aggregate_id=aggregate_id,
                        title="Técnico sin trabajo asignado",
                        message=f"El técnico {aggregate_id} acumula {minutes} minutos sin OT activa.",
                        detected_at=detected_at,
                        payload=payload,
                    )
                )

        if event_type == "CASH_CLOSING_RECORDED":
            try:
                difference = Decimal(str(payload.get("difference", "0")))
            except InvalidOperation:
                difference = Decimal("0")
            if difference != 0:
                alerts.append(
                    Alert(
                        code="CASH_DIFFERENCE",
                        severity="critical",
                        aggregate_id=aggregate_id,
                        title="Diferencia en cierre de caja",
                        message=f"El cierre {aggregate_id} presenta una diferencia de L {difference:.2f}.",
                        detected_at=detected_at,
                        payload=payload,
                    )
                )

        if event_type == "QUALITY_CHECK_FAILED":
            alerts.append(
                Alert(
                    code="QUALITY_CHECK_FAILED",
                    severity="critical",
                    aggregate_id=aggregate_id,
                    title="Control de calidad rechazado",
                    message=f"La orden {aggregate_id} debe regresar a reparación antes de entregarse.",
                    detected_at=detected_at,
                    payload=payload,
                )
            )

        return alerts
