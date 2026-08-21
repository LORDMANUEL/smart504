from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_URL = os.environ.get("API_URL", "http://haproxy:8082").rstrip("/")
HEARTBEAT_TOKEN = os.environ["HEARTBEAT_TOKEN"]
ADMIN_TOKEN = os.environ["ADMIN_API_TOKEN"]
NODE_ID = os.environ.get("NODE_ID", socket.gethostname())
LEASE_NAME = os.environ.get("LEASE_NAME", "alerts-worker")
INTERVAL = max(5, int(os.environ.get("POLL_INTERVAL_SECONDS", "15")))
STATE = {"mode": "starting", "last_error": None, "fencing_token": None}


def post(path: str, payload: dict[str, object], heartbeat: bool = False) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    headers["X-Heartbeat-Token" if heartbeat else "X-Admin-Token"] = (
        HEARTBEAT_TOKEN if heartbeat else ADMIN_TOKEN
    )
    request = urllib.request.Request(
        f"{API_URL}{path}",
        data=json.dumps(payload).encode(),
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def get(path: str) -> tuple[int, object]:
    request = urllib.request.Request(
        f"{API_URL}{path}", headers={"X-Admin-Token": ADMIN_TOKEN}
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        return response.status, json.loads(response.read())


def evaluate_rules() -> None:
    status, board = get("/api/v1/operations/work-orders/board")
    if status != 200:
        raise RuntimeError("board unavailable")
    counts = {column["status"]: len(column["work_orders"]) for column in board}
    print(f"leader={NODE_ID} fencing={STATE['fencing_token']} counts={counts}", flush=True)


def worker_loop() -> None:
    while True:
        try:
            status, lease = post(
                f"/api/v1/cluster/leases/{LEASE_NAME}",
                {"node_id": NODE_ID, "ttl_seconds": INTERVAL * 3},
                heartbeat=True,
            )
            if status == 200:
                STATE.update(mode="leader", fencing_token=lease["fencing_token"], last_error=None)
                evaluate_rules()
            elif status == 409:
                STATE.update(mode="standby", fencing_token=None, last_error=None)
            else:
                raise RuntimeError(f"lease HTTP {status}")
            post(
                "/api/v1/cluster/heartbeats",
                {
                    "node_id": NODE_ID,
                    "role": "alerts-worker",
                    "status": "HEALTHY",
                    "version": os.environ.get("APP_VERSION", "0.4.0"),
                    "metadata": {"mode": STATE["mode"], "fencing_token": STATE["fencing_token"]},
                },
                heartbeat=True,
            )
        except Exception as exc:
            STATE.update(mode="degraded", last_error=type(exc).__name__)
            print(f"alerts worker error={type(exc).__name__}", flush=True)
        time.sleep(INTERVAL)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(STATE).encode()
        self.send_response(200 if STATE["mode"] != "degraded" else 503)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def main() -> None:
    threading.Thread(target=worker_loop, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8090), Handler).serve_forever()


if __name__ == "__main__":
    main()
