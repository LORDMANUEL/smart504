from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


def deterministic_event_key(event_type: str, aggregate_id: str, discriminator: str = "") -> str:
    raw = "|".join((event_type.strip().upper(), aggregate_id.strip(), discriminator.strip()))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_id: str
    event_key: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    actor_id: str | None
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: dict[str, Any],
        actor_id: str | None = None,
        discriminator: str | None = None,
    ) -> "DomainEvent":
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        resolved_discriminator = discriminator or hashlib.sha256(canonical_payload.encode()).hexdigest()
        return cls(
            event_id=str(uuid.uuid4()),
            event_key=deterministic_event_key(event_type, aggregate_id, resolved_discriminator),
            event_type=event_type.strip().upper(),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            actor_id=actor_id,
            occurred_at=datetime.now(UTC),
        )
