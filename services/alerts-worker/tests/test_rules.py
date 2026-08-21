from datetime import UTC, datetime, timedelta

from smartdiag_alerts.rules import AlertRuleEngine


NOW = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)


def test_promised_work_order_past_due_creates_critical_alert() -> None:
    event = {
        "event_type": "WORK_ORDER_SNAPSHOT",
        "aggregate_id": "SO-0001",
        "payload": {"status": "IN_PROGRESS", "promised_at": (NOW - timedelta(hours=2)).isoformat()},
    }
    alerts = AlertRuleEngine().evaluate(event, NOW)
    assert any(a.code == "WORK_ORDER_OVERDUE" and a.severity == "critical" for a in alerts)


def test_pending_quote_over_48_hours_creates_warning() -> None:
    event = {
        "event_type": "QUOTE_SNAPSHOT",
        "aggregate_id": "SQ-0001",
        "payload": {"status": "SENT", "sent_at": (NOW - timedelta(hours=49)).isoformat()},
    }
    alerts = AlertRuleEngine().evaluate(event, NOW)
    assert any(a.code == "QUOTE_UNANSWERED" for a in alerts)


def test_cash_difference_creates_critical_alert() -> None:
    event = {
        "event_type": "CASH_CLOSING_RECORDED",
        "aggregate_id": "POS-0001",
        "payload": {"difference": "125.00"},
    }
    alerts = AlertRuleEngine().evaluate(event, NOW)
    assert any(a.code == "CASH_DIFFERENCE" and a.severity == "critical" for a in alerts)


def test_part_request_pending_over_two_hours_creates_warning() -> None:
    event = {
        "event_type": "PART_REQUEST_SNAPSHOT",
        "aggregate_id": "PR-0001",
        "payload": {"status": "PENDING", "requested_at": (NOW - timedelta(hours=3)).isoformat()},
    }
    alerts = AlertRuleEngine().evaluate(event, NOW)
    assert any(a.code == "PART_REQUEST_DELAYED" and a.severity == "warning" for a in alerts)


def test_idle_technician_over_one_hour_creates_warning() -> None:
    event = {
        "event_type": "TECHNICIAN_SNAPSHOT",
        "aggregate_id": "EMP-0001",
        "payload": {"status": "IDLE", "idle_since": (NOW - timedelta(minutes=75)).isoformat()},
    }
    alerts = AlertRuleEngine().evaluate(event, NOW)
    assert any(a.code == "TECHNICIAN_IDLE" for a in alerts)
