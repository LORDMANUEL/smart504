from __future__ import annotations

import json

from app.config import get_settings
from app.db import SessionLocal
from app.services.erp_sync import process_erp_jobs


def main() -> None:
    with SessionLocal() as db:
        result = process_erp_jobs(db, get_settings())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
