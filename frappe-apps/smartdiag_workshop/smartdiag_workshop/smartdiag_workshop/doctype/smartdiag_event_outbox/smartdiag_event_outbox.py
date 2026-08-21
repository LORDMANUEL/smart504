from __future__ import annotations

import json

from frappe.model.document import Document


class SmartDiagEventOutbox(Document):
    def validate(self):
        json.loads(self.payload_json or "{}")

    def payload_envelope(self) -> str:
        return json.dumps(
            {
                "event_type": self.event_type,
                "aggregate_type": self.aggregate_type,
                "aggregate_id": self.aggregate_id,
                "actor_id": self.actor_id,
                "payload": json.loads(self.payload_json or "{}"),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
