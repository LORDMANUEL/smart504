from __future__ import annotations

from io import BytesIO

from openpyxl import load_workbook


def test_admin_can_download_and_preview_catalog_template(client, admin_headers) -> None:
    template = client.get("/api/v1/operations/catalog-import/template", headers=admin_headers)
    assert template.status_code == 200
    assert template.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    workbook = load_workbook(BytesIO(template.content))
    workbook["Mano de obra"].append(
        [
            "MO-001",
            "Diagnóstico electrónico",
            "Toyota",
            "Corolla",
            2010,
            2025,
            "",
            1,
            400,
            750,
            "SI",
        ]
    )
    output = BytesIO()
    workbook.save(output)

    preview = client.post(
        "/api/v1/operations/catalog-import/preview",
        headers=admin_headers,
        files={
            "file": (
                "catalogo.xlsx",
                output.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert preview.status_code == 200
    assert preview.json()["summary"] == {"labor": 1, "parts": 0, "errors": 0}


def test_catalog_preview_rejects_non_xlsx(client, admin_headers) -> None:
    response = client.post(
        "/api/v1/operations/catalog-import/preview",
        headers=admin_headers,
        files={"file": ("catalogo.csv", b"codigo,descripcion", "text/csv")},
    )
    assert response.status_code == 422


def test_demo_template_contains_requested_catalog(client, admin_headers) -> None:
    template = client.get(
        "/api/v1/operations/catalog-import/template?demo=true", headers=admin_headers
    )
    assert template.status_code == 200

    preview = client.post(
        "/api/v1/operations/catalog-import/preview",
        headers=admin_headers,
        files={
            "file": (
                "catalogo_demo.xlsx",
                template.content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert preview.status_code == 200
    assert preview.json()["summary"] == {"labor": 5, "parts": 9, "errors": 0}
    assert all(len(item["fitments"]) == 3 for item in preview.json()["labor"])
