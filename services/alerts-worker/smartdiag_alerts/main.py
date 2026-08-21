from __future__ import annotations

import os

from .worker import RedisAlertWorker, run_demo


def main() -> None:
    if os.getenv("ALERTS_MODE", "redis").casefold() == "demo":
        run_demo()
    RedisAlertWorker().run_forever()


if __name__ == "__main__":
    main()
