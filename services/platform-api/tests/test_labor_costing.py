from decimal import Decimal

from app.models import Customer, StaffUser, Vehicle


def _work_order(client, admin_headers, db) -> dict:
    customer = Customer(full_name="Cliente mano de obra", phone="99990044")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(
        customer_id=customer.id,
        make="Ford",
        model="Escape",
        model_year=2020,
        vin="1FMCU0G6XLUA99991",
    )
    db.add(vehicle)
    db.commit()
    response = client.post(
        "/api/v1/operations/work-orders",
        headers=admin_headers,
        json={
            "customer_id": customer.id,
            "vehicle_id": vehicle.id,
            "title": "Diagnostico especializado",
            "concern": "Calcular mano de obra por tecnico y especialidad.",
            "actor": "asesor-demo",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_fixed_salary_and_hourly_wages_price_labor_without_exposing_salary(
    client, admin_headers, db
) -> None:
    technician = StaffUser(
        email="labor.tech@example.com",
        hashed_password="not-used-in-this-test",
        employee_code="TEC-LAB-01",
        full_name="Tecnico de laboratorio",
        job_title="Tecnico especialista",
        role="TECHNICIAN",
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    db.add(technician)
    db.commit()

    compensation = client.put(
        f"/api/v1/staff/users/{technician.id}/compensation",
        headers=admin_headers,
        json={
            "fixed_monthly_salary": "18000.00",
            "productive_hours_monthly": "176.00",
            "base_hourly_wage": "40.00",
            "specialized_hourly_wage": "120.00",
            "employer_burden_percent": "35.00",
            "standard_sale_rate": "450.00",
            "specialized_sale_rate": "850.00",
            "currency": "HNL",
            "effective_from": "2026-08-01",
        },
    )
    assert compensation.status_code == 200
    profile = compensation.json()
    assert Decimal(profile["fixed_hourly_allocation"]).quantize(Decimal("0.01")) == Decimal("102.27")
    assert Decimal(profile["standard_hourly_cost"]).quantize(Decimal("0.01")) == Decimal("192.07")
    assert Decimal(profile["specialized_hourly_cost"]).quantize(Decimal("0.01")) == Decimal("300.07")

    work_order = _work_order(client, admin_headers, db)
    recorded = client.post(
        f"/api/v1/operations/work-orders/{work_order['id']}/labor-entries",
        headers=admin_headers,
        json={
            "technician_id": str(technician.id),
            "service_code": "MO-DIAG-001",
            "description": "Este texto del cliente no debe sustituir el catálogo",
            "rate_kind": "SPECIALIZED",
            "hours": "2.50",
            "actor": "jefe-taller",
        },
    )
    assert recorded.status_code == 201
    labor = recorded.json()
    assert labor["technician_name"] == technician.full_name
    assert Decimal(labor["hourly_sale_rate"]) == Decimal("850.00")
    assert labor["description"] == "Diagnóstico electrónico completo"
    assert Decimal(labor["hours"]) == Decimal("1.500")
    assert Decimal(labor["sale_total"]) == Decimal("1275.00000")
    assert labor["actor"] == "system-recovery"
    assert "fixed_monthly_salary" not in labor
    assert "hourly_cost" not in labor

    quote = client.post(
        f"/api/v1/operations/finance/quotes/from-work-order/{work_order['id']}",
        headers=admin_headers,
        json={"actor": "asesor-demo"},
    )
    assert quote.status_code == 201
    line = quote.json()["lines"][0]
    assert line["code"] == "MO-DIAG-001"
    assert Decimal(line["quantity"]) == Decimal("1.500")
    assert Decimal(line["unit_price"]) == Decimal("850.00")
    assert Decimal(line["unit_cost"]).quantize(Decimal("0.01")) == Decimal("300.07")


def test_labor_rate_below_real_hourly_cost_is_rejected(client, admin_headers, db) -> None:
    technician = StaffUser(
        email="labor.floor@example.com",
        hashed_password="not-used-in-this-test",
        employee_code="TEC-LAB-02",
        full_name="Tecnico costo minimo",
        role="TECHNICIAN",
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    db.add(technician)
    db.commit()
    response = client.put(
        f"/api/v1/staff/users/{technician.id}/compensation",
        headers=admin_headers,
        json={
            "fixed_monthly_salary": "22000",
            "productive_hours_monthly": "160",
            "base_hourly_wage": "50",
            "specialized_hourly_wage": "140",
            "employer_burden_percent": "40",
            "standard_sale_rate": "100",
            "specialized_sale_rate": "200",
            "currency": "HNL",
            "effective_from": "2026-08-01",
        },
    )
    assert response.status_code == 422
    assert "costo real" in response.json()["detail"]
