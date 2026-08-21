from __future__ import annotations

from datetime import date, timedelta
import uuid


def test_unlinked_employee_overview_is_an_actionable_empty_state(client, admin_headers) -> None:
    suffix = uuid.uuid4().hex[:8]
    email = f"unlinked-{suffix}@example.com"
    created = client.post("/api/v1/staff/users", headers=admin_headers, json={
        "email": email, "password": "Temporal-504-Segura!", "full_name": "Técnico sin contrato",
        "job_title": "Técnico", "role": "TECHNICIAN", "permissions_json": [],
        "is_active": True, "is_verified": True,
    })
    assert created.status_code == 201
    assert client.post("/api/v1/staff/auth/login", data={
        "username": email, "password": "Temporal-504-Segura!",
    }).status_code == 204
    overview = client.get("/api/v1/staff/self-service/overview")
    assert overview.status_code == 200
    assert overview.json() == {
        "linked": False, "contract": None, "today_attendance": None,
        "leave_requests": [], "vouchers": [],
    }


def test_versioned_deductions_vouchers_and_prestations(client, admin_headers) -> None:
    suffix = uuid.uuid4().hex[:8]
    policy = client.post("/api/v1/operations/enterprise/hr/payroll-policies", headers=admin_headers, json={
        "code": f"HN-{suffix.upper()}", "name": "Regla validada por contador", "effective_from": "2026-01-01",
        "source_reference": "Acta contador 2026-01 y fuente oficial SETRASS",
        "rules": [{"code": "SEGURO_EMPLOYEE", "label": "Seguro empleado", "side": "EMPLOYEE_DEDUCTION", "calculation": "PERCENT", "rate": "5", "enabled": True}],
    })
    assert policy.status_code == 201
    contract = client.post("/api/v1/operations/enterprise/hr/contracts", headers=admin_headers, json={
        "employee_name": "Empleado planilla Honduras", "date_of_birth": "1992-05-20", "national_id": f"0801-{suffix}",
        "address": "Tegucigalpa, Honduras", "job_title": "Tecnico", "contract_type": "PERMANENT",
        "start_date": "2024-01-01", "monthly_salary": "20000", "payment_type": "WEEKLY", "base_pay_amount": "5000",
        "standard_hours_weekly": "44", "currency": "HNL",
    })
    assert contract.status_code == 201
    assert contract.json()["employee_code"].startswith("EMP-")
    payroll = client.post("/api/v1/operations/enterprise/hr/payroll-runs", headers=admin_headers, json={
        "period_start": "2026-08-03", "period_end": "2026-08-09", "contract_ids": [contract.json()["id"]],
    })
    assert payroll.status_code == 201
    assert payroll.json()["gross_total"] == "5000.00"
    assert payroll.json()["deduction_total"] == "250.00"
    vouchers = client.get("/api/v1/operations/enterprise/hr/payroll-vouchers", headers=admin_headers)
    assert vouchers.status_code == 200
    voucher = next(item for item in vouchers.json() if item["contract_id"] == contract.json()["id"])
    assert voucher["net"] == "4750.00"
    preview = client.post("/api/v1/operations/enterprise/hr/prestations/preview", headers=admin_headers, json={
        "contract_id": contract.json()["id"], "termination_date": "2026-08-17", "average_ordinary_monthly": "20000",
        "include_notice": True, "include_severance": True,
    })
    assert preview.status_code == 200
    assert float(preview.json()["estimated_total"]) > 0
    assert preview.json()["vacation_days"]


def test_technician_can_mark_time_request_leave_and_see_own_portal(client, admin_headers) -> None:
    suffix = uuid.uuid4().hex[:8]
    email = f"tech-self-{suffix}@example.com"
    user = client.post("/api/v1/staff/users", headers=admin_headers, json={
        "email": email, "password": "Temporal-504-Segura!", "full_name": "Tecnico autoservicio",
        "job_title": "Tecnico", "role": "TECHNICIAN", "permissions_json": [], "is_active": True, "is_verified": True,
    })
    assert user.status_code == 201
    assert user.json()["employee_code"].startswith("EMP-")
    contract = client.post("/api/v1/operations/enterprise/hr/contracts", headers=admin_headers, json={
        "employee_name": "Tecnico autoservicio", "email": email, "date_of_birth": "1995-02-10", "national_id": f"0801-{suffix}",
        "address": "Comayaguela, Honduras", "job_title": "Tecnico", "contract_type": "PERMANENT",
        "start_date": "2026-01-01", "monthly_salary": "18000", "payment_type": "MONTHLY", "base_pay_amount": "18000",
        "standard_hours_weekly": "44", "currency": "HNL",
    })
    assert contract.status_code == 201
    assert contract.json()["employee_code"] == user.json()["employee_code"]
    payroll = client.post("/api/v1/operations/enterprise/hr/payroll-runs", headers=admin_headers, json={
        "period_start": "2026-08-01", "period_end": "2026-08-31", "contract_ids": [contract.json()["id"]],
    })
    assert payroll.status_code == 201
    decision_users = []
    for role in ("MANAGER", "OWNER"):
        decision_email = f"payroll-{role.lower()}-{suffix}@example.com"
        created = client.post("/api/v1/staff/users", headers=admin_headers, json={
            "email": decision_email, "password": "Temporal-504-Segura!", "full_name": f"Responsable {role}",
            "job_title": role, "role": role, "permissions_json": [], "is_active": True, "is_verified": True,
        })
        assert created.status_code == 201
        decision_users.append(decision_email)
    for status, decision_email in zip(("REVIEWED", "APPROVED"), decision_users, strict=True):
        login_decider = client.post("/api/v1/staff/auth/login", data={"username": decision_email, "password": "Temporal-504-Segura!"})
        assert login_decider.status_code == 204
        payroll = client.patch(
            f"/api/v1/operations/enterprise/hr/payroll-runs/{payroll.json()['id']}/status",
            json={"status": status},
        )
        assert payroll.status_code == 200
    login = client.post("/api/v1/staff/auth/login", data={"username": email, "password": "Temporal-504-Segura!"})
    assert login.status_code == 204
    overview = client.get("/api/v1/staff/self-service/overview")
    assert overview.status_code == 200
    assert overview.json()["linked"] is True
    assert overview.json()["contract"]["id"] == contract.json()["id"]
    assert len(overview.json()["vouchers"]) == 1
    voucher_html = client.get(f"/api/v1/staff/self-service/vouchers/{overview.json()['vouchers'][0]['id']}/html")
    assert voucher_html.status_code == 200
    assert "Imprimir o guardar PDF" in voucher_html.text
    assert voucher_html.headers["cache-control"] == "private, no-store"
    check_in = client.post("/api/v1/staff/self-service/punch", json={"action": "CHECK_IN"})
    assert check_in.status_code == 200
    check_out = client.post("/api/v1/staff/self-service/punch", json={"action": "CHECK_OUT"})
    assert check_out.status_code == 200
    start = date.today() + timedelta(days=5)
    leave = client.post("/api/v1/staff/self-service/leave-requests", json={
        "leave_type": "PERSONAL", "start_date": start.isoformat(), "end_date": start.isoformat(), "reason": "Tramite personal",
    })
    assert leave.status_code == 200
    assert leave.json()["requested_by"] == user.json()["employee_code"]
