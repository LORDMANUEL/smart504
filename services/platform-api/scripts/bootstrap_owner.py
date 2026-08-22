from __future__ import annotations

import os
import uuid

from fastapi_users.password import PasswordHelper
from sqlalchemy import select

from app.db import SessionLocal
from app.models import StaffUser


def main() -> None:
    email = os.environ["INITIAL_OWNER_EMAIL"].strip().lower()
    password = os.environ["INITIAL_OWNER_PASSWORD"]
    full_name = os.getenv("INITIAL_OWNER_NAME", "Propietario SmartDiag504").strip()
    if len(password) < 16:
        raise RuntimeError("INITIAL_OWNER_PASSWORD must contain at least 16 characters")

    with SessionLocal() as db:
        existing = db.scalar(select(StaffUser).where(StaffUser.email == email))
        if existing is not None:
            print(f"Initial owner already exists: {existing.employee_code}")
            return
        user = StaffUser(
            id=uuid.uuid4(),
            email=email,
            hashed_password=PasswordHelper().hash(password),
            is_active=True,
            is_superuser=True,
            is_verified=True,
            organization_id=os.getenv("INITIAL_ORGANIZATION_ID", "SMARTDIAG504"),
            branch_id=None,
            employee_code="EMP-0001",
            full_name=full_name,
            job_title="Propietario",
            role="OWNER",
            permissions_json=["*"],
            session_version=1,
        )
        db.add(user)
        db.commit()
        print("Initial owner created: EMP-0001")


if __name__ == "__main__":
    main()
