from __future__ import annotations

import uuid


ROLE_PASSWORD = "Rol-Seguro-504!"


def _create_role_user(client, admin_headers, *, role: str, suffix: str):
    return client.post(
        "/api/v1/staff/users",
        headers=admin_headers,
        json={
            "email": f"{role.lower()}.{suffix}@example.com",
            "password": ROLE_PASSWORD,
            "employee_code": f"{role[:3]}-{suffix}".upper(),
            "full_name": f"Usuario {role}",
            "role": role,
            "permissions_json": [],
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
        },
    )


def _login(client, email: str):
    return client.post(
        "/api/v1/staff/auth/login",
        data={"username": email, "password": ROLE_PASSWORD},
    )


def test_enterprise_overview_filters_domains_by_role(client, admin_headers) -> None:
    suffix = uuid.uuid4().hex[:8]
    supplier = client.post(
        "/api/v1/operations/enterprise/suppliers",
        headers=admin_headers,
        json={"code": f"SEC-{suffix}", "name": "Proveedor confidencial", "currency": "HNL"},
    )
    contract = client.post(
        "/api/v1/operations/enterprise/hr/contracts",
        headers=admin_headers,
        json={
            "employee_name": "Empleado confidencial",
            "date_of_birth": "1990-01-15",
            "job_title": "Tecnico",
            "contract_type": "PERMANENT",
            "start_date": "2026-08-01",
            "monthly_salary": "18000.00",
            "standard_hours_weekly": "44.00",
            "currency": "HNL",
        },
    )
    channel = client.post(
        "/api/v1/operations/enterprise/social/channels",
        headers=admin_headers,
        json={
            "channel_type": "WHATSAPP",
            "name": f"Canal {suffix}",
            "external_account_id": f"wa-{suffix}",
            "credential_reference": f"secret://wa/{suffix}",
        },
    )
    assert supplier.status_code == contract.status_code == channel.status_code == 201

    marketing = _create_role_user(client, admin_headers, role="MARKETING", suffix=suffix)
    assert marketing.status_code == 201, marketing.text
    assert _login(client, marketing.json()["email"]).status_code == 204
    marketing_view = client.get("/api/v1/operations/enterprise/overview")
    assert marketing_view.status_code == 200
    assert marketing_view.json()["suppliers"] == []
    assert marketing_view.json()["contracts"] == []
    assert len(marketing_view.json()["social_channels"]) == 1
    assert client.post("/api/v1/staff/auth/logout").status_code == 204

    accountant = _create_role_user(client, admin_headers, role="ACCOUNTANT", suffix=f"a{suffix}")
    assert accountant.status_code == 201, accountant.text
    assert _login(client, accountant.json()["email"]).status_code == 204
    accountant_view = client.get("/api/v1/operations/enterprise/overview")
    assert accountant_view.status_code == 200
    assert len(accountant_view.json()["suppliers"]) == 1
    assert len(accountant_view.json()["contracts"]) == 1
    assert accountant_view.json()["social_channels"] == []


def test_procurement_import_hr_used_and_social_vertical_slices(client, admin_headers) -> None:
    suffix = uuid.uuid4().hex[:8]

    supplier = client.post(
        "/api/v1/operations/enterprise/suppliers",
        headers=admin_headers,
        json={
            "code": f"SUP-{suffix}",
            "name": "Proveedor integral de prueba",
            "tax_id": f"RTN-{suffix}",
            "email": f"compras-{suffix}@example.com",
            "phone": "99990000",
            "payment_terms_days": 30,
            "currency": "HNL",
        },
    )
    assert supplier.status_code == 201
    supplier_updated = client.patch(
        f"/api/v1/operations/enterprise/suppliers/{supplier.json()['id']}",
        headers=admin_headers,
        json={"payment_terms_days": 45, "phone": "99991111", "active": True},
    )
    assert supplier_updated.status_code == 200
    assert supplier_updated.json()["payment_terms_days"] == 45

    purchase = client.post(
        "/api/v1/operations/enterprise/purchase-orders",
        headers=admin_headers,
        json={
            "supplier_id": supplier.json()["id"],
            "currency": "USD",
            "expected_at": "2026-09-15T14:00:00Z",
            "items": [{"sku": "FILTRO-001", "description": "Filtro de aceite", "quantity": "10", "unit_cost": "8.50"}],
            "notes": "Compra para inventario",
        },
    )
    assert purchase.status_code == 201
    assert purchase.json()["status"] == "DRAFT"
    submitted = client.patch(
        f"/api/v1/operations/enterprise/purchase-orders/{purchase.json()['id']}/status",
        headers=admin_headers,
        json={"status": "SUBMITTED"},
    )
    assert submitted.status_code == 200
    assert submitted.json()["erp_sync_status"] == "PENDING"
    approved = client.patch(
        f"/api/v1/operations/enterprise/purchase-orders/{purchase.json()['id']}/status",
        headers=admin_headers,
        json={"status": "APPROVED"},
    )
    assert approved.status_code == 200
    received = client.post(
        f"/api/v1/operations/enterprise/purchase-orders/{purchase.json()['id']}/receipts",
        headers=admin_headers,
        json={"items": [{"sku": "FILTRO-001", "quantity": "4"}], "reference": f"REC-{suffix}", "note": "Recepcion parcial verificada"},
    )
    assert received.status_code == 200
    assert received.json()["status"] == "PARTIALLY_RECEIVED"
    assert received.json()["items_json"][0]["received_quantity"] == "4"

    import_case = client.post(
        "/api/v1/operations/enterprise/import-cases",
        headers=admin_headers,
        json={
            "purchase_order_id": purchase.json()["id"],
            "incoterm": "CIF",
            "origin_country": "US",
            "destination_port": "Puerto Cortes",
            "eta": "2026-09-20T12:00:00Z",
            "costs": [{"kind": "FREIGHT", "description": "Flete maritimo", "amount": "250.00", "currency": "USD"}],
        },
    )
    assert import_case.status_code == 201
    assert import_case.json()["status"] == "PLANNED"
    import_updated = client.patch(
        f"/api/v1/operations/enterprise/import-cases/{import_case.json()['id']}",
        headers=admin_headers,
        json={
            "costs": [
                {"kind": "FREIGHT", "description": "Flete maritimo", "amount": "250.00", "currency": "USD"},
                {"kind": "CUSTOMS", "description": "Agencia aduanera", "amount": "85.00", "currency": "USD"},
            ],
            "documents": [{"kind": "BILL_OF_LADING", "name": "BL prueba", "url": "https://files.example.test/bl.pdf"}],
        },
    )
    assert import_updated.status_code == 200
    assert import_updated.json()["additional_cost_total"] == "335.00"

    contract = client.post(
        "/api/v1/operations/enterprise/hr/contracts",
        headers=admin_headers,
        json={
            "employee_code": f"TEC-{suffix}",
            "employee_name": "Tecnico de prueba",
            "date_of_birth": "1990-01-15",
            "job_title": "Tecnico especialista",
            "contract_type": "PERMANENT",
            "start_date": "2026-08-01",
            "monthly_salary": "18000.00",
            "standard_hours_weekly": "44.00",
            "currency": "HNL",
        },
    )
    assert contract.status_code == 201
    attendance = client.post(
        "/api/v1/operations/enterprise/hr/attendance",
        headers=admin_headers,
        json={"contract_id": contract.json()["id"], "work_date": "2026-08-17", "regular_hours": "8", "overtime_hours": "1"},
    )
    assert attendance.status_code == 201
    overtime = client.patch(
        f"/api/v1/operations/enterprise/hr/attendance/{attendance.json()['id']}/overtime",
        headers=admin_headers,
        json={"status": "APPROVED", "note": "Trabajo autorizado en OT de emergencia"},
    )
    assert overtime.status_code == 200
    assert overtime.json()["overtime_status"] == "APPROVED"
    contract_updated = client.patch(
        f"/api/v1/operations/enterprise/hr/contracts/{contract.json()['id']}",
        headers=admin_headers,
        json={"job_title": "Tecnico senior", "monthly_salary": "19000.00", "schedule": {"monday": ["08:00", "17:00"]}},
    )
    assert contract_updated.status_code == 200
    assert contract_updated.json()["job_title"] == "Tecnico senior"
    payroll = client.post(
        "/api/v1/operations/enterprise/hr/payroll-runs",
        headers=admin_headers,
        json={
            "period_start": "2026-08-01", "period_end": "2026-08-31", "contract_ids": [contract.json()["id"]],
            "adjustments": [{"contract_id": contract.json()["id"], "kind": "COMMISSION", "description": "Comision aprobada", "amount": "500.00"}],
        },
    )
    assert payroll.status_code == 201
    assert payroll.json()["status"] == "DRAFT"
    assert float(payroll.json()["gross_total"]) > 19500

    used = client.post(
        "/api/v1/operations/enterprise/used-vehicles",
        headers=admin_headers,
        json={
            "vin": f"USED{suffix.upper()}1234567",
            "make": "Honda",
            "model": "Civic",
            "model_year": 2008,
            "acquisition_type": "CONSIGNMENT",
            "acquisition_cost": "120000.00",
            "target_sale_price": "145000.00",
            "mileage_km": 165000,
            "owner_name": "Propietario de prueba",
        },
    )
    assert used.status_code == 201
    assert used.json()["status"] == "APPRAISAL"

    channel = client.post(
        "/api/v1/operations/enterprise/social/channels",
        headers=admin_headers,
        json={"channel_type": "WHATSAPP", "name": "WhatsApp Taller", "external_account_id": f"wa-{suffix}", "credential_reference": f"secret://wa/{suffix}"},
    )
    assert channel.status_code == 201
    conversation = client.post(
        "/api/v1/operations/enterprise/social/conversations",
        headers=admin_headers,
        json={"channel_id": channel.json()["id"], "contact_name": "Cliente social", "contact_handle": "+50499990000", "consent_status": "OPTED_IN", "subject": "Consulta de repuesto"},
    )
    assert conversation.status_code == 201
    message = client.post(
        f"/api/v1/operations/enterprise/social/conversations/{conversation.json()['id']}/messages",
        headers=admin_headers,
        json={"direction": "OUTBOUND", "body": "Su solicitud fue recibida.", "human_approved": True},
    )
    assert message.status_code == 201
    assert message.json()["status"] == "QUEUED"

    overview = client.get("/api/v1/operations/enterprise/overview", headers=admin_headers)
    assert overview.status_code == 200
    counts = overview.json()["counts"]
    for key in (
        "suppliers", "purchase_orders", "import_cases", "contracts",
        "used_vehicles", "social_conversations",
    ):
        assert counts[key] >= 1
