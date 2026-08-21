from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_URL = os.environ.get("API_URL", "http://haproxy:8082").rstrip("/")
TOKEN = os.environ["HEARTBEAT_TOKEN"]
NODE_ID = os.environ.get("NODE_ID", socket.gethostname())
ROLE = os.environ.get("NODE_ROLE", "application-replica")
VERSION = os.environ.get("APP_VERSION", "0.4.0")
INTERVAL = max(5, int(os.environ.get("HEARTBEAT_INTERVAL_SECONDS", "10")))
TARGET_HEALTH_URL = os.environ.get("TARGET_HEALTH_URL")
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8091"))
STATE: dict[str, object] = {
    "status": "starting",
    "node_id": NODE_ID,
    "role": ROLE,
    "last_success_at": None,
    "last_error": None,
}


def target_status() -> tuple[str, dict[str, object]]:
    metadata: dict[str, object] = {
        "hostname": socket.gethostname(),
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    if not TARGET_HEALTH_URL:
        return "HEALTHY", metadata
    try:
        with urllib.request.urlopen(TARGET_HEALTH_URL, timeout=4) as response:
            metadata["target_http_status"] = response.status
            return ("HEALTHY" if response.status < 400 else "DEGRADED"), metadata
    except Exception as exc:  # network boundary
        metadata["target_error"] = type(exc).__name__
        return "UNHEALTHY", metadata


def send() -> str:
    status, metadata = target_status()
    payload = json.dumps(
        {
            "node_id": NODE_ID,
            "role": ROLE,
            "status": status,
            "version": VERSION,
            "metadata": metadata,
        }
    ).encode()
    request = urllib.request.Request(
        f"{API_URL}/api/v1/cluster/heartbeats",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "X-Heartbeat-Token": TOKEN},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status >= 400:
            raise RuntimeError(f"heartbeat returned HTTP {response.status}")
    return status


def heartbeat_loop() -> None:
    while True:
        try:
            status = send()
            STATE.update(
                status=status.casefold(),
                last_success_at=datetime.now(timezone.utc).isoformat(),
                last_error=None,
            )
            print(f"heartbeat sent node={NODE_ID} status={status}", flush=True)
        except Exception as exc:  # network boundary
            STATE.update(status="degraded", last_error=type(exc).__name__)
            print(f"heartbeat failed node={NODE_ID} error={type(exc).__name__}", flush=True)
        time.sleep(INTERVAL)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(STATE).encode()
        code = 200 if STATE["status"] not in {"degraded", "unhealthy"} else 503
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler).serve_forever()


if __name__ == "__main__":
    main()
