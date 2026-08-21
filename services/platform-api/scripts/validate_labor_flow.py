"""Idempotent live validation for compensation -> OT labor -> quote."""

import httpx

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    headers = {"X-Admin-Token": settings.admin_api_token.get_secret_value()}
    with httpx.Client(base_url="http://127.0.0.1:8000", headers=headers, timeout=20) as client:
        technicians = client.get("/api/v1/staff/technicians").raise_for_status().json()
        if not technicians:
            raise RuntimeError("No active technicians are configured")
        technician = technicians[0]

        customers = client.get("/api/v1/operations/customers").raise_for_status().json()
        customer = next((item for item in customers if item["full_name"] == "Cliente demo costeo laboral"), None)
        if customer is None:
            customer = client.post(
                "/api/v1/operations/customers",
                json={"full_name": "Cliente demo costeo laboral", "phone": "+504 9999-5040"},
            ).raise_for_status().json()

        vehicles = client.get(
            "/api/v1/operations/vehicles", params={"customer_id": customer["id"]}
        ).raise_for_status().json()
        vehicle = next((item for item in vehicles if item.get("vin") == "LABORDEMO20260814"), None)
        if vehicle is None:
            vehicle = client.post(
                "/api/v1/operations/vehicles",
                json={
                    "customer_id": customer["id"],
                    "vin": "LABORDEMO20260814",
                    "plate": "MO504",
                    "make": "Ford",
                    "model": "Escape",
                    "model_year": 2020,
                    "mileage_km": 75000,
                },
            ).raise_for_status().json()

        work_orders = client.get("/api/v1/operations/work-orders").raise_for_status().json()
        work_order = next(
            (item for item in work_orders if item["vehicle_id"] == vehicle["id"] and item["title"] == "Demo costeo mano de obra"),
            None,
        )
        if work_order is None:
            work_order = client.post(
                "/api/v1/operations/work-orders",
                json={
                    "customer_id": customer["id"],
                    "vehicle_id": vehicle["id"],
                    "title": "Demo costeo mano de obra",
                    "concern": "Validar salario fijo, hora normal y especializada.",
                    "assigned_technicians": [technician["full_name"]],
                    "actor": "validacion-vps",
                },
            ).raise_for_status().json()

        labor = client.get(
            f"/api/v1/operations/work-orders/{work_order['id']}/labor-entries"
        ).raise_for_status().json()
        entry = next((item for item in labor if item["service_code"] == "MO-DEMO-ESP"), None)
        if entry is None:
            entry = client.post(
                f"/api/v1/operations/work-orders/{work_order['id']}/labor-entries",
                json={
                    "technician_id": technician["id"],
                    "service_code": "MO-DEMO-ESP",
                    "description": "Diagnostico electronico especializado",
                    "rate_kind": "SPECIALIZED",
                    "hours": "1.50",
                    "actor": "validacion-vps",
                },
            ).raise_for_status().json()

        quotes = client.get("/api/v1/operations/finance/quotes").raise_for_status().json()
        quote = next(
            (
                item
                for item in quotes
                if item.get("work_order_id") == work_order["id"]
                and any(line["code"] == "MO-DEMO-ESP" for line in item["lines"])
            ),
            None,
        )
        if quote is None:
            quote = client.post(
                f"/api/v1/operations/finance/quotes/from-work-order/{work_order['id']}",
                json={"actor": "validacion-vps"},
            ).raise_for_status().json()
        print(
            {
                "work_order": work_order["external_reference"],
                "labor_hours": entry["hours"],
                "labor_sale_total": entry["sale_total"],
                "quote": quote["number"],
                "quote_total": quote["total"],
            }
        )


if __name__ == "__main__":
    main()
