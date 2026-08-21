from __future__ import annotations

import os
from pathlib import Path

TEST_ROOT = Path("/tmp/smartdiag504-platform-api-tests")
TEST_ROOT.mkdir(parents=True, exist_ok=True)
DB_PATH = TEST_ROOT / "test.db"
if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["MEDIA_ROOT"] = str(TEST_ROOT / "media")
os.environ["PRIVATE_EVIDENCE_ROOT"] = str(TEST_ROOT / "private-evidence")
os.environ["PUBLIC_MEDIA_BASE_URL"] = "/media"
os.environ["ADMIN_API_TOKEN"] = "test-admin-token"
os.environ["EVENT_HMAC_SECRET"] = "test-heartbeat-token"
os.environ["ENVIRONMENT"] = "test"
os.environ["INVOICE_VERIFICATION_MODE"] = "development"
os.environ["FRAPPE_REQUIRED"] = "false"
os.environ["CORS_ORIGINS"] = "http://testserver"
# Production secrets from Compose must not change isolated test behavior.
os.environ.pop("CASHIER_ACCESS_CODE", None)
os.environ.pop("REDIS_URL", None)

import pytest
import uuid
from fastapi.testclient import TestClient
from fastapi_users.password import PasswordHelper

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import Branch, ClientUser, Customer, LaborCatalogItem, Vehicle


@pytest.fixture(scope="session", autouse=True)
def database_schema() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        session.add(
            Branch(
                organization_id="SMARTDIAG504",
                code="MAIN",
                name="Sucursal principal de pruebas",
                active=True,
            )
        )
        for code, description, hours, cost, price in (
            ("MO-DIAG-001", "Diagnóstico electrónico completo", 1.5, 650, 1200),
            ("MO-ACEITE-001", "Cambio de aceite y filtro", 0.7, 280, 650),
            ("MO-FRENOS-001", "Servicio de frenos delanteros", 2.0, 900, 1850),
            ("MO-SUSP-001", "Inspección y ajuste de suspensión", 1.2, 520, 1100),
            ("MO-AC-001", "Diagnóstico de aire acondicionado", 1.0, 450, 950),
        ):
            session.add(LaborCatalogItem(
                organization_id="SMARTDIAG504", code=code, description=description,
                standard_hours=hours, internal_cost=cost, sale_price=price,
                vehicle_rules=[], erp_item_code=code,
            ))
        session.commit()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def client_account(db):
    """Create a real linked portal identity and vehicle for one isolated test."""
    suffix = uuid.uuid4().hex[:10]
    email = f"cliente-{suffix}@example.com"
    password = "Cliente-seguro-504!"
    customer = Customer(full_name="Cliente Portal", phone=f"+5049{suffix[:7]}", email=email)
    db.add(customer)
    db.flush()
    vehicle = Vehicle(customer_id=customer.id, vin=f"TESTVIN{suffix.upper()}", plate=f"T{suffix[:6].upper()}",
                      make="Ford", model="Escape", model_year=2020, mileage_km=80000)
    db.add(vehicle)
    db.flush()
    db.add(ClientUser(email=email, hashed_password=PasswordHelper().hash(password), is_active=True,
                      is_verified=True, is_superuser=False, organization_id=customer.organization_id,
                      customer_id=customer.id, username=f"cliente.{suffix}", full_name=customer.full_name))
    db.commit()
    return {"email": email, "password": password, "customer": customer, "vehicle": vehicle}


@pytest.fixture()
def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": "test-admin-token"}


@pytest.fixture()
def heartbeat_headers() -> dict[str, str]:
    return {"X-Heartbeat-Token": "test-heartbeat-token"}
