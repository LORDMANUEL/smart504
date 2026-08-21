from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from .rules import AlertRuleEngine


class RedisAlertWorker:
    def __init__(self) -> None:
        try:
            import redis
        except ImportError as exc:  # pragma: no cover - production dependency
            raise RuntimeError("Install redis to run the alerts worker") from exc
        self.redis = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis-platform:6379/0"), decode_responses=True
        )
        self.stream = os.getenv("EVENT_STREAM", "smartdiag:events")
        self.group = os.getenv("ALERT_GROUP", "smartdiag-alerts")
        self.consumer = os.getenv("HOSTNAME", "alerts-1")
        self.output_stream = os.getenv("ALERT_STREAM", "smartdiag:alerts")
        self.engine = AlertRuleEngine()
        try:
            self.redis.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def run_forever(self) -> None:
        heartbeat = Path("/tmp/smartdiag-alerts.heartbeat")
        while True:
            heartbeat.touch()
            messages = self.redis.xreadgroup(
                self.group,
                self.consumer,
                {self.stream: ">"},
                count=20,
                block=5000,
            )
            for _, entries in messages:
                for message_id, fields in entries:
                    self._process(message_id, fields)

    def _process(self, message_id: str, fields: dict[str, Any]) -> None:
        event = json.loads(fields.get("event", "{}"))
        for alert in self.engine.evaluate(event):
            self.redis.xadd(
                self.output_stream,
                {"alert": json.dumps(alert.__dict__, default=str, ensure_ascii=False)},
                maxlen=10000,
                approximate=True,
            )
        self.redis.xack(self.stream, self.group, message_id)


def run_demo() -> None:
    heartbeat = Path("/tmp/smartdiag-alerts.heartbeat")
    while True:
        heartbeat.touch()
        time.sleep(30)
