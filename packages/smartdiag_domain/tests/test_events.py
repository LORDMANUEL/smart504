from smartdiag_domain.events import DomainEvent, deterministic_event_key


def test_event_key_is_stable_for_same_business_event() -> None:
    first = deterministic_event_key("WORK_ORDER_STATUS_CHANGED", "SO-0001", "IN_PROGRESS")
    second = deterministic_event_key("WORK_ORDER_STATUS_CHANGED", "SO-0001", "IN_PROGRESS")
    assert first == second
    assert len(first) == 64


def test_domain_event_builds_required_envelope() -> None:
    event = DomainEvent.create(
        event_type="WORK_ORDER_CREATED",
        aggregate_type="Service Order",
        aggregate_id="SO-0001",
        payload={"vehicle": "SDV-0001"},
        actor_id="user@example.com",
    )
    assert event.event_id
    assert event.event_key
    assert event.occurred_at.tzinfo is not None
