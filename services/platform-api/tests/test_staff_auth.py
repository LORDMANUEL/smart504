from fastapi.testclient import TestClient
from urllib.parse import unquote
import re
from sqlalchemy import select

from app.auth import _permission_for_path
from app.main import app
from app.models import NotificationDelivery
from app.services.staff_security import totp_code
from app.staff_auth import has_permission
from types import SimpleNamespace


OWNER_PASSWORD = "Owner-Demo-504!"
TECH_PASSWORD = "Tecnico-Demo-504!"


def test_operational_roles_cannot_mutate_catalog_or_document_templates() -> None:
    technician = SimpleNamespace(role="TECHNICIAN", permissions_json=[])
    warehouse = SimpleNamespace(role="WAREHOUSE", permissions_json=[])
    accountant = SimpleNamespace(role="ACCOUNTANT", permissions_json=[])
    assert has_permission(technician, "DOCUMENTS", "GET")
    assert not has_permission(technician, "DOCUMENTS", "POST")
    assert has_permission(technician, "CATALOG", "GET")
    assert not has_permission(technician, "CATALOG", "PATCH")
    assert has_permission(warehouse, "CATALOG", "PATCH")
    assert has_permission(accountant, "DOCUMENTS", "POST")


def test_counter_return_retry_uses_cashier_permission() -> None:
    assert _permission_for_path("/api/v1/operations/finance/counter-returns/demo/sync") == "CASHIER"


def test_heatmap_read_is_available_to_every_authenticated_role() -> None:
    assert _permission_for_path("/api/v1/operations/flow-events/heatmap") == "AUTHENTICATED"
    assert _permission_for_path("/api/v1/operations/flow-events") == "PROCESSES"


def test_staff_session_probe_is_quiet_when_signed_out(client) -> None:
    assert client.get("/api/v1/staff/session").status_code == 204


def login(client: TestClient, email: str, password: str, mfa_code: str | None = None):
    data = {"username": email, "password": password}
    if mfa_code:
        data["client_secret"] = mfa_code
    return client.post(
        "/api/v1/staff/auth/login",
        data=data,
    )


def create_owner(client, admin_headers, *, email: str, employee_code: str):
    return client.post(
        "/api/v1/staff/users",
        headers=admin_headers,
        json={
            "email": email,
            "password": OWNER_PASSWORD,
            "employee_code": employee_code,
            "full_name": "Propietario seguridad",
            "role": "OWNER",
            "permissions_json": [],
            "is_active": True,
            "is_superuser": True,
            "is_verified": True,
        },
    )


def test_staff_lockout_mfa_and_session_revocation(client, admin_headers) -> None:
    email = "owner.security@example.com"
    assert create_owner(client, admin_headers, email=email, employee_code="OWN-SEC").status_code == 201
    assert login(client, email, OWNER_PASSWORD).status_code == 204
    enrollment = client.post("/api/v1/staff/me/mfa/enroll")
    assert enrollment.status_code == 200
    code = totp_code(enrollment.json()["secret"])
    assert client.post("/api/v1/staff/me/mfa/confirm", json={"code": code}).status_code == 204
    assert client.get("/api/v1/staff/me").status_code == 401
    assert login(client, email, OWNER_PASSWORD).status_code == 400
    assert login(client, email, OWNER_PASSWORD, code).status_code == 204
    assert client.post("/api/v1/staff/me/sessions/revoke").status_code == 204
    assert client.get("/api/v1/staff/me").status_code == 401

    locked_email = "owner.locked@example.com"
    assert create_owner(
        client, admin_headers, email=locked_email, employee_code="OWN-LOCK"
    ).status_code == 201
    for _ in range(5):
        assert login(client, locked_email, "Wrong-Password-504!").status_code == 400
    assert login(client, locked_email, OWNER_PASSWORD).status_code == 400


def test_staff_password_reset_is_queued_and_consumable(client, admin_headers, db) -> None:
    email = "owner.password.reset@example.com"
    assert create_owner(client, admin_headers, email=email, employee_code="OWN-RESET").status_code == 201

    requested = client.post("/api/v1/staff/auth/forgot-password", json={"email": email})
    assert requested.status_code == 202
    db.expire_all()
    delivery = db.scalar(
        select(NotificationDelivery)
        .where(
            NotificationDelivery.recipient == email,
            NotificationDelivery.template_key == "STAFF_PASSWORD_RESET",
        )
        .order_by(NotificationDelivery.created_at.desc())
    )
    assert delivery is not None
    assert delivery.status == "PENDING"
    match = re.search(r"reset_token=([^\s]+)", delivery.body_text)
    assert match is not None
    reset_token = unquote(match.group(1))

    new_password = "Owner-New-Password-504!"
    reset = client.post(
        "/api/v1/staff/auth/reset-password",
        json={"token": reset_token, "password": new_password},
    )
    assert reset.status_code == 200
    assert login(client, email, OWNER_PASSWORD).status_code == 400
    assert login(client, email, new_password).status_code == 204


def test_staff_cookie_login_rbac_and_access_audit(client, admin_headers) -> None:
    owner = client.post(
        "/api/v1/staff/users",
        headers=admin_headers,
        json={
            "email": "owner.staff@example.com",
            "password": OWNER_PASSWORD,
            "employee_code": "OWN-001",
            "full_name": "Propietario de prueba",
            "job_title": "Propietario",
            "role": "OWNER",
            "permissions_json": [],
            "is_active": True,
            "is_superuser": True,
            "is_verified": True,
        },
    )
    assert owner.status_code == 201
    assert "hashed_password" not in owner.json()

    session = login(client, "owner.staff@example.com", OWNER_PASSWORD)
    assert session.status_code == 204
    cookie = session.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "smartdiag_staff_session=" in cookie

    profile = client.get("/api/v1/staff/me")
    assert profile.status_code == 200
    assert profile.json()["role"] == "OWNER"

    technician = client.post(
        "/api/v1/staff/users",
        json={
            "email": "tecnico.staff@example.com",
            "password": TECH_PASSWORD,
            "employee_code": "TEC-001",
            "full_name": "Tecnico de prueba",
            "job_title": "Tecnico automotriz",
            "role": "TECHNICIAN",
            "permissions_json": [],
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
        },
    )
    assert technician.status_code == 201
    cashier = client.post(
        "/api/v1/staff/users",
        json={
            "email": "cashier.staff@example.com",
            "password": TECH_PASSWORD,
            "employee_code": "CAJ-001",
            "full_name": "Cajera de prueba",
            "job_title": "Caja",
            "role": "CASHIER",
            "permissions_json": [],
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
        },
    )
    assert cashier.status_code == 201

    assert client.post("/api/v1/staff/auth/logout").status_code == 204
    assert login(client, "tecnico.staff@example.com", TECH_PASSWORD).status_code == 204
    assert client.get("/api/v1/operations/work-orders/board").status_code == 200
    denied = client.get("/api/v1/operations/finance/cash-summary")
    assert denied.status_code == 403
    assert "CASHIER" in denied.json()["detail"]
    assert client.post(
        "/api/v1/operations/customers",
        json={"full_name": "Cliente no autorizado", "phone": "99990000"},
    ).status_code == 403
    assert client.patch(
        "/api/v1/operations/work-orders/no-existe",
        json={"diagnosis": "El tecnico si puede intentar editar"},
    ).status_code == 404

    assert client.post("/api/v1/staff/auth/logout").status_code == 204
    assert login(client, "cashier.staff@example.com", TECH_PASSWORD).status_code == 204
    assert client.patch(
        "/api/v1/operations/work-orders/no-existe",
        json={"diagnosis": "Caja no debe editar diagnosticos"},
    ).status_code == 403

    with TestClient(app) as recovery_client:
        events = recovery_client.get("/api/v1/staff/access-events", headers=admin_headers)
        assert events.status_code == 200
        assert sum(item["action"] == "LOGIN" for item in events.json()) >= 2


def test_staff_manager_is_strictly_isolated_to_own_organization(client, admin_headers) -> None:
    owner_a = client.post(
        "/api/v1/staff/users",
        headers=admin_headers,
        json={
            "email": "owner.tenant.a@example.com",
            "password": OWNER_PASSWORD,
            "organization_id": "TENANT_A",
            "employee_code": "OWN-A",
            "full_name": "Propietario tenant A",
            "role": "OWNER",
            "permissions_json": [],
            "is_active": True,
            "is_superuser": True,
            "is_verified": True,
        },
    )
    owner_b = client.post(
        "/api/v1/staff/users",
        headers=admin_headers,
        json={
            "email": "owner.tenant.b@example.com",
            "password": OWNER_PASSWORD,
            "organization_id": "TENANT_B",
            "employee_code": "OWN-B",
            "full_name": "Propietario tenant B",
            "role": "OWNER",
            "permissions_json": [],
            "is_active": True,
            "is_superuser": True,
            "is_verified": True,
        },
    )
    assert owner_a.status_code == 201
    assert owner_b.status_code == 201

    assert login(client, "owner.tenant.a@example.com", OWNER_PASSWORD).status_code == 204
    visible_users = client.get("/api/v1/staff/users")
    assert visible_users.status_code == 200
    assert {item["organization_id"] for item in visible_users.json()} == {"TENANT_A"}

    created = client.post(
        "/api/v1/staff/users",
        json={
            "email": "technician.tenant.a@example.com",
            "password": TECH_PASSWORD,
            "organization_id": "TENANT_B",
            "employee_code": "TEC-A",
            "full_name": "Tecnico tenant A",
            "role": "TECHNICIAN",
            "permissions_json": [],
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
        },
    )
    assert created.status_code == 201
    assert created.json()["organization_id"] == "TENANT_A"

    customer_a = client.post(
        "/api/v1/operations/customers",
        json={"full_name": "Cliente privado A", "phone": "99990001"},
    )
    assert customer_a.status_code == 201
    vehicle_a = client.post(
        "/api/v1/operations/vehicles",
        json={
            "customer_id": customer_a.json()["id"],
            "vin": "1HGBH41JXMN109186",
            "make": "Honda",
            "model": "Civic",
            "model_year": 2008,
        },
    )
    assert vehicle_a.status_code == 201
    work_order_a = client.post(
        "/api/v1/operations/work-orders",
        json={
            "number": "OT-SHARED-0001",
            "customer_id": customer_a.json()["id"],
            "vehicle_id": vehicle_a.json()["id"],
            "title": "OT privada tenant A",
            "concern": "No debe ser visible fuera de la empresa",
            "actor": "dato-no-autoritativo",
        },
    )
    assert work_order_a.status_code == 201
    cash_a = client.post(
        "/api/v1/operations/finance/cash-sessions",
        json={"opening_balance": "100", "actor": "dato-no-autoritativo"},
    )
    assert cash_a.status_code == 201

    assert client.post("/api/v1/staff/auth/logout").status_code == 204
    assert login(client, "owner.tenant.b@example.com", OWNER_PASSWORD).status_code == 204
    customer_b = client.post(
        "/api/v1/operations/customers",
        json={"full_name": "Cliente privado B", "phone": "99990002"},
    )
    assert customer_b.status_code == 201
    vehicle_b = client.post(
        "/api/v1/operations/vehicles",
        json={
            "customer_id": customer_b.json()["id"],
            "vin": "1HGBH41JXMN109186",
            "make": "Honda",
            "model": "Civic",
            "model_year": 2008,
        },
    )
    assert vehicle_b.status_code == 201
    assert client.get(f"/api/v1/operations/work-orders/{work_order_a.json()['id']}").status_code == 404
    assert all(
        card["id"] != work_order_a.json()["id"]
        for column in client.get("/api/v1/operations/work-orders/board").json()
        for card in column["work_orders"]
    )
    assert client.get("/api/v1/operations/finance/cash-sessions/current").json() is None
    cash_b = client.post(
        "/api/v1/operations/finance/cash-sessions",
        json={"opening_balance": "200", "actor": "dato-no-autoritativo"},
    )
    assert cash_b.status_code == 201
    assert cash_b.json()["id"] != cash_a.json()["id"]
    work_order_b = client.post(
        "/api/v1/operations/work-orders",
        json={
            "number": "OT-SHARED-0001",
            "customer_id": customer_b.json()["id"],
            "vehicle_id": vehicle_b.json()["id"],
            "title": "OT privada tenant B",
            "concern": "Mismo consecutivo permitido en otra empresa",
            "actor": "dato-no-autoritativo",
        },
    )
    assert work_order_b.status_code == 201
    visible_b = client.get("/api/v1/operations/customers")
    assert {item["full_name"] for item in visible_b.json()} == {"Cliente privado B"}
    assert {item["id"] for item in client.get("/api/v1/operations/vehicles").json()} == {
        vehicle_b.json()["id"]
    }

    assert client.post("/api/v1/staff/auth/logout").status_code == 204
    assert login(client, "owner.tenant.a@example.com", OWNER_PASSWORD).status_code == 204
    visible_a = client.get("/api/v1/operations/customers")
    assert {item["full_name"] for item in visible_a.json()} == {"Cliente privado A"}
    assert {item["id"] for item in client.get("/api/v1/operations/vehicles").json()} == {
        vehicle_a.json()["id"]
    }
    assert client.get(f"/api/v1/operations/work-orders/{work_order_b.json()['id']}").status_code == 404
    assert client.get("/api/v1/operations/finance/cash-sessions/current").json()["id"] == cash_a.json()["id"]

    foreign_update = client.patch(
        f"/api/v1/staff/users/{owner_b.json()['id']}",
        json={"full_name": "No debe cambiar"},
    )
    assert foreign_update.status_code == 404

    foreign_compensation = client.put(
        f"/api/v1/staff/users/{owner_b.json()['id']}/compensation",
        json={
            "fixed_monthly_salary": "10000",
            "productive_hours_monthly": "176",
            "base_hourly_wage": "0",
            "specialized_hourly_wage": "0",
            "employer_burden_percent": "0",
            "standard_sale_rate": "100",
            "specialized_sale_rate": "120",
            "currency": "HNL",
            "effective_from": "2026-08-14",
        },
    )
    assert foreign_compensation.status_code == 404
