from app.models import Customer, Vehicle
import pytest


def create_quote(client, admin_headers, db) -> dict:
    customer = Customer(full_name="Cliente Documento", phone="99995555", email="docs@example.com")
    db.add(customer)
    db.flush()
    vehicle = Vehicle(
        customer_id=customer.id,
        make="Ford",
        model="Escape",
        model_year=2020,
        vin="1FMCU0G6XLUA99999",
        plate="HDOC001",
    )
    db.add(vehicle)
    db.commit()
    work_order = client.post(
        "/api/v1/operations/work-orders",
        headers=admin_headers,
        json={
            "customer_id": customer.id,
            "vehicle_id": vehicle.id,
            "title": "Servicio con documento configurable",
            "concern": "Validar formato HTML y PDF.",
            "actor": "asesor-documentos",
        },
    )
    assert work_order.status_code == 201
    quote = client.post(
        "/api/v1/operations/finance/quotes",
        headers=admin_headers,
        json={
            "work_order_id": work_order.json()["id"],
            "created_by": "asesor-documentos",
            "discount": "0.00",
            "tax": "0.00",
            "lines": [{
                "line_type": "LABOR",
                "code": "MO-DOC-001",
                "description": "Diagnostico electronico documentado",
                "quantity": "1",
                "unit_price": "850.00",
                "unit_cost": "350.00",
            }],
        },
    )
    assert quote.status_code == 201
    return quote.json()


def test_template_is_versioned_published_and_used_by_quote_pdf(client, admin_headers, db) -> None:
    html_template = (
        "<header><h1>EMPRESA PERSONALIZADA</h1></header>"
        "<h2>{{ document.number }}</h2><p>{{ customer.name }}</p>"
        "<table><tbody>{{ quote.rows_html }}</tbody></table>"
        "<strong>{{ quote.total }}</strong>"
    )
    created = client.post(
        "/api/v1/operations/documents/templates",
        headers=admin_headers,
        json={
            "code": "TEST_QUOTE_PERSONALIZED",
            "name": "Cotizacion personalizada de prueba",
            "document_type": "QUOTE",
            "paper_size": "LETTER",
            "html_template": html_template,
            "css_text": "body{font-family:Helvetica,sans-serif}",
            "change_note": "Formato inicial validado",
            "created_by": "administrador-test",
        },
    )
    assert created.status_code == 201
    template = created.json()
    assert template["current_version"] == 1
    assert "document.number" in template["versions"][0]["variables_json"]

    version = client.post(
        f"/api/v1/operations/documents/templates/{template['id']}/versions",
        headers=admin_headers,
        json={
            "paper_size": "LETTER",
            "html_template": html_template.replace("EMPRESA PERSONALIZADA", "EMPRESA PERSONALIZADA V2"),
            "css_text": "body{font-family:Helvetica,sans-serif;color:#111}",
            "change_note": "Segunda version aprobada",
            "created_by": "administrador-test",
        },
    )
    assert version.status_code == 201
    assert version.json()["version"] == 2

    published = client.post(
        f"/api/v1/operations/documents/templates/{template['id']}/publish",
        headers=admin_headers,
        json={"version": 2, "actor": "administrador-test"},
    )
    assert published.status_code == 200
    assert published.json()["published_version"] == 2

    quote = create_quote(client, admin_headers, db)
    printable = client.get(
        f"/api/v1/operations/finance/quotes/{quote['id']}.html",
        headers=admin_headers,
    )
    assert printable.status_code == 200
    assert "EMPRESA PERSONALIZADA V2" in printable.text
    assert quote["number"] in printable.text

    pdf = client.get(
        f"/api/v1/operations/finance/quotes/{quote['id']}.pdf",
        headers=admin_headers,
    )
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")

    history = client.get(
        f"/api/v1/operations/documents/renders?reference={quote['number']}",
        headers=admin_headers,
    )
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["template_id"] == template["id"]
    assert len(history.json()[0]["content_sha256"]) == 64


def test_preview_rejects_active_content(client, admin_headers) -> None:
    response = client.post(
        "/api/v1/operations/documents/preview",
        headers=admin_headers,
        json={
            "paper_size": "LETTER",
            "html_template": "<section>Documento seguro</section><script>alert(1)</script>",
            "css_text": "body{color:#111}",
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize("html_template,css_text", [
    ('<img src="file:///etc/passwd" alt="x">', ""),
    ('<img src="http://127.0.0.1:8080/private" alt="x">', ""),
    ("<section style=\"background:url(file:///etc/passwd)\">x</section>", ""),
    ("<section>seguro</section>", "body{background:url(http://169.254.169.254/latest/meta-data)}"),
    ("<svg><use href='file:///etc/passwd'></use></svg>", ""),
])
def test_preview_rejects_local_and_external_resources(client, admin_headers, html_template, css_text) -> None:
    response = client.post("/api/v1/operations/documents/preview", headers=admin_headers, json={
        "paper_size": "LETTER", "html_template": html_template, "css_text": css_text,
    })
    assert response.status_code == 422


def test_template_can_be_replaced_from_html_and_css_files(client, admin_headers) -> None:
    created = client.post(
        "/api/v1/operations/documents/templates/import",
        headers=admin_headers,
        data={
            "code": "INVOICE_UPLOAD_TEST",
            "name": "Factura subida por archivo",
            "document_type": "INVOICE",
            "paper_size": "LETTER",
            "change_note": "Carga inicial del contador",
        },
        files={
            "html_file": ("factura.html", b"<h1>{{ company.name }}</h1><p>{{ document.number }}</p>", "text/html"),
            "css_file": ("factura.css", b"body{font-family:Arial;color:#111}", "text/css"),
        },
    )
    assert created.status_code == 201
    template = created.json()
    assert template["current_version"] == 1

    replaced = client.post(
        "/api/v1/operations/documents/templates/import",
        headers=admin_headers,
        data={
            "template_id": template["id"],
            "code": template["code"],
            "name": template["name"],
            "document_type": "INVOICE",
            "paper_size": "THERMAL_80",
            "change_note": "Formato termico reemplazado",
        },
        files={"html_file": ("factura-v2.html", b"<h1>V2 {{ document.number }}</h1>", "text/html")},
    )
    assert replaced.status_code == 201
    assert replaced.json()["current_version"] == 2
    assert replaced.json()["versions"][0]["paper_size"] == "THERMAL_80"

    exported = client.get(
        f"/api/v1/operations/documents/templates/{template['id']}/export",
        headers=admin_headers,
    )
    assert exported.status_code == 200
    assert exported.json()["template"]["organization_id"] == "SMARTDIAG504"
    assert exported.json()["versions"][0]["version"] == 2
