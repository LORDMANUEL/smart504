#!/usr/bin/env bash
set -euo pipefail
curl -fsS --max-time 2 http://127.0.0.1/ready >/dev/null
curl -fsS --max-time 2 http://127.0.0.1/ >/dev/null
