from __future__ import annotations

from io import BytesIO

from PIL import Image


def valid_png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (64, 64), "#ED111C").save(output, format="PNG")
    return output.getvalue()


def test_branding_can_be_updated_uploaded_and_used_in_document_preview(client, admin_headers) -> None:
    public_default = client.get("/api/v1/branding")
    assert public_default.status_code == 200
    assert public_default.json()["organization_id"] == "SMARTDIAG504"

    updated = client.put(
        "/api/v1/operations/settings/branding",
        headers=admin_headers,
        json={
            "display_name": "Taller Personalizado 504",
            "legal_name": "Taller Personalizado 504, S. de R.L.",
            "tax_id": "08011999123456",
            "address": "Tegucigalpa, Honduras",
            "phone": "+504 2222-5040",
            "email": "contacto@example.com",
            "website": "https://taller.example.com",
            "primary_color": "#123456",
            "accent_color": "#C0392B",
            "surface_color": "#FFFFFF",
            "text_color": "#17202A",
            "document_footer": "Gracias por confiar en nuestro taller.",
            "seasonal_theme_enabled": True,
            "seasonal_theme_code": "PATRIA_SEPTEMBER",
            "seasonal_theme_title": "Mes de la patria",
            "seasonal_theme_message": "Celebramos Honduras y Centroamérica",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["primary_color"] == "#123456"
    assert updated.json()["seasonal_theme_code"] == "PATRIA_SEPTEMBER"

    uploaded = client.post(
        "/api/v1/operations/settings/branding/assets",
        headers=admin_headers,
        data={"asset_type": "LOGO"},
        files={"file": ("logo.png", valid_png(), "image/png")},
    )
    assert uploaded.status_code == 201
    logo_url = uploaded.json()["logo_url"]
    assert logo_url.startswith("/media/branding/SMARTDIAG504/logo-")
    assert uploaded.json()["asset_history"][-1]["asset_type"] == "LOGO"

    media = client.get(logo_url)
    assert media.status_code == 200
    assert media.headers["content-type"].startswith("image/png")

    public_profile = client.get("/api/v1/branding")
    assert public_profile.json()["display_name"] == "Taller Personalizado 504"
    assert public_profile.json()["logo_url"] == logo_url
    assert public_profile.json()["asset_history"] == []

    preview = client.post(
        "/api/v1/operations/documents/preview",
        headers=admin_headers,
        json={
            "paper_size": "LETTER",
            "html_template": "<img src='{{ company.logo_data_uri }}' alt=''><h1>{{ company.name }}</h1><p>{{ company.document_footer }}</p>",
            "css_text": "body{font-family:Arial}h1{color:{{ company.primary_color }}}",
        },
    )
    assert preview.status_code == 200
    assert "Taller Personalizado 504" in preview.text
    assert "#123456" in preview.text
    assert "data:image/png;base64," in preview.text


def test_branding_rejects_invalid_colors_and_active_image_formats(client, admin_headers) -> None:
    current = client.get("/api/v1/operations/settings/branding", headers=admin_headers).json()
    invalid = client.put(
        "/api/v1/operations/settings/branding",
        headers=admin_headers,
        json={**{key: current[key] for key in (
            "display_name", "legal_name", "tax_id", "address", "phone", "email", "website",
            "primary_color", "accent_color", "surface_color", "text_color", "document_footer",
        )}, "primary_color": "red"},
    )
    assert invalid.status_code == 422

    svg = client.post(
        "/api/v1/operations/settings/branding/assets",
        headers=admin_headers,
        data={"asset_type": "LOGO"},
        files={"file": ("logo.svg", b"<svg><script>alert(1)</script></svg>", "image/svg+xml")},
    )
    assert svg.status_code == 415
