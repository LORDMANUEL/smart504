"""Create reversible demo costing profiles for active technicians without overwriting real data."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.db import SessionLocal
from app.models import StaffCompensationProfile, StaffUser


def main() -> None:
    created = 0
    with SessionLocal() as db:
        technicians = list(
            db.scalars(
                select(StaffUser).where(
                    StaffUser.role == "TECHNICIAN", StaffUser.is_active.is_(True)
                )
            )
        )
        for technician in technicians:
            existing = db.scalar(
                select(StaffCompensationProfile).where(
                    StaffCompensationProfile.staff_user_id == technician.id
                )
            )
            if existing is not None:
                continue
            db.add(
                StaffCompensationProfile(
                    organization_id=technician.organization_id,
                    staff_user_id=technician.id,
                    fixed_monthly_salary=Decimal("18000.00"),
                    productive_hours_monthly=Decimal("176.00"),
                    base_hourly_wage=Decimal("40.00"),
                    specialized_hourly_wage=Decimal("120.00"),
                    employer_burden_percent=Decimal("35.00"),
                    standard_sale_rate=Decimal("450.00"),
                    specialized_sale_rate=Decimal("850.00"),
                    currency="HNL",
                    effective_from=date(2026, 8, 1),
                    source_system="DEMO_SEED",
                )
            )
            created += 1
        db.commit()
    print({"technicians_found": len(technicians), "demo_profiles_created": created})


if __name__ == "__main__":
    main()
