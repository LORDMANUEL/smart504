from __future__ import annotations

import json

from app.config import get_settings
from app.db import SessionLocal
from app.services.notifications import deliver_notifications


if __name__ == "__main__":
    with SessionLocal() as db:
        result = deliver_notifications(db, get_settings())
    print(json.dumps(result, sort_keys=True))
