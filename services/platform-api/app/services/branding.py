from __future__ import annotations

import base64
from datetime import UTC, datetime
from mimetypes import guess_type
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import WorkshopSetting

DEFAULT_ORGANIZATION_ID = "SMARTDIAG504"
DEFAULT_BRANDING: dict[str, object] = {
    "display_name": "SmartDiag504",
    "legal_name": "SmartDiag504",
    "tax_id": "",
    "address": "Tegucigalpa, Honduras",
    "phone": "",
    "email": "info@smartdiag504.com",
    "website": "https://taller.nexusmedi.org",
    "primary_color": "#ED111C",
    "accent_color": "#C3000B",
    "surface_color": "#FFFFFF",
    "text_color": "#17181C",
    "logo_url": "/brand/smartdiag504-logo.png",
    "logo_dark_url": "/brand/smartdiag504-logo.png",
    "favicon_url": "/brand/smartdiag504-logo.png",
    "document_footer": "Documento generado desde la trazabilidad registrada en SmartDiag504.",
    "asset_history": [],
}


def branding_key(organization_id: str) -> str:
    return f"branding:{organization_id}"


def load_branding(db: Session, organization_id: str = DEFAULT_ORGANIZATION_ID) -> dict[str, object]:
    setting = db.get(WorkshopSetting, branding_key(organization_id))
    value = dict(DEFAULT_BRANDING)
    if setting:
        value.update(setting.value or {})
    value["organization_id"] = organization_id
    value["updated_at"] = setting.updated_at.isoformat() if setting and setting.updated_at else None
    return value


def save_branding(db: Session, organization_id: str, values: dict[str, object]) -> dict[str, object]:
    key = branding_key(organization_id)
    setting = db.get(WorkshopSetting, key)
    stored = dict(DEFAULT_BRANDING)
    if setting:
        stored.update(setting.value or {})
    stored.update(values)
    stored.pop("organization_id", None)
    stored.pop("updated_at", None)
    if setting is None:
        setting = WorkshopSetting(key=key, value=stored)
        db.add(setting)
    else:
        setting.value = stored
    db.flush()
    return load_branding(db, organization_id)


def record_asset_version(
    profile: dict[str, object], *, asset_type: str, url: str, actor: str
) -> list[dict[str, object]]:
    history = list(profile.get("asset_history") or [])
    history.append({
        "asset_type": asset_type,
        "url": url,
        "actor": actor,
        "created_at": datetime.now(UTC).isoformat(),
    })
    return history[-30:]


def branding_template_context(profile: dict[str, object]) -> dict[str, object]:
    return {
        "company.name": profile["display_name"],
        "company.legal_name": profile["legal_name"],
        "company.tax_id": profile["tax_id"],
        "company.address": profile["address"],
        "company.phone": profile["phone"],
        "company.email": profile["email"],
        "company.website": profile["website"],
        "company.logo_url": profile["logo_url"],
        "company.logo_dark_url": profile["logo_dark_url"],
        "company.logo_data_uri": _local_asset_data_uri(str(profile["logo_url"])),
        "company.primary_color": profile["primary_color"],
        "company.accent_color": profile["accent_color"],
        "company.document_footer": profile["document_footer"],
    }


def _local_asset_data_uri(public_url: str) -> str:
    """Embed locally stored brand assets so PDF engines do not need network access."""
    settings = get_settings()
    prefix = settings.public_media_base_url.rstrip("/") + "/"
    if not public_url.startswith(prefix):
        return ""
    relative = public_url.removeprefix(prefix)
    candidate = (settings.media_root / relative).resolve()
    media_root = Path(settings.media_root).resolve()
    if media_root not in candidate.parents or not candidate.is_file():
        return ""
    mime = guess_type(candidate.name)[0] or "application/octet-stream"
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        return ""
    encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
