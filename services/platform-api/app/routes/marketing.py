from __future__ import annotations

import hashlib
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.config import get_settings
from app.db import get_db
from app.models import FlowEvent, StaffUser, WorkshopSetting
from app.request_context import audit_actor
from app.services.malware import scan_bytes

admin_router = APIRouter(prefix="/api/v1/operations/marketing", tags=["marketing"], dependencies=[Depends(require_admin)])
public_router = APIRouter(tags=["marketing-public"])
SETTING_KEY = "marketing_campaigns"


class CampaignCreate(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=4, max_length=1000)
    audience: str = Field(default="Todos los vehículos", max_length=300)
    valid_from: str | None = Field(default=None, max_length=30)
    valid_until: str | None = Field(default=None, max_length=30)
    price_from: int | None = Field(default=None, ge=0, le=10000000)
    call_to_action: str = Field(default="Agenda hoy", min_length=2, max_length=80)
    tv_enabled: bool = True
    display_seconds: int = Field(default=12, ge=5, le=120)


def _campaigns(db: Session) -> tuple[WorkshopSetting, list[dict[str, object]]]:
    setting = db.get(WorkshopSetting, SETTING_KEY) or WorkshopSetting(key=SETTING_KEY, value={"items": []})
    # Work with detached dictionaries so SQLAlchemy can compare the new JSON value
    # and persist status/media changes instead of missing an in-place mutation.
    return setting, deepcopy(list(setting.value.get("items", [])))


def _with_clicks(db: Session, items: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = dict(db.execute(select(FlowEvent.item_reference, func.count(FlowEvent.id)).where(FlowEvent.module == "MARKETING", FlowEvent.action == "CAMPAIGN_CLICK").group_by(FlowEvent.item_reference)).all())
    return [{**item, "clicks": counts.get(str(item["id"]), 0), "public_path": f"/c/{item['slug']}"} for item in items]


def _is_current(item: dict[str, object]) -> bool:
    today = datetime.now(UTC).date().isoformat()
    valid_from = str(item.get("valid_from") or "")
    valid_until = str(item.get("valid_until") or "")
    return (not valid_from or valid_from <= today) and (not valid_until or valid_until >= today)


@admin_router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    _, items = _campaigns(db); return _with_clicks(db, items)


@admin_router.post("/campaigns", status_code=status.HTTP_201_CREATED)
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    setting, items = _campaigns(db); identifier = str(uuid.uuid4()); base = slugify(data.title)[:60] or "campania"
    campaign = {"id": identifier, **data.model_dump(), "slug": f"{base}-{identifier[:7]}", "status": "DRAFT", "media_url": None,
                "media_type": None, "created_at": datetime.now(UTC).isoformat()}
    items.insert(0, campaign); setting.value = {"items": items}; db.add(setting); db.commit()
    return {**campaign, "clicks": 0, "public_path": f"/c/{campaign['slug']}"}


def _find(items: list[dict[str, object]], campaign_id: str) -> dict[str, object]:
    campaign = next((item for item in items if item.get("id") == campaign_id), None)
    if campaign is None: raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return campaign


def _validate_media(raw: bytes, content_type: str) -> None:
    if content_type.startswith("image/"):
        try:
            with Image.open(BytesIO(raw)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, SyntaxError) as exc:
            raise HTTPException(status_code=422, detail="La imagen no es válida") from exc
        return
    is_mp4 = content_type == "video/mp4" and len(raw) >= 12 and raw[4:8] == b"ftyp"
    is_webm = content_type == "video/webm" and raw.startswith(b"\x1aE\xdf\xa3")
    if not (is_mp4 or is_webm):
        raise HTTPException(status_code=422, detail="El video no coincide con el formato indicado")


@admin_router.post("/campaigns/{campaign_id}/publish")
def publish_campaign(
    campaign_id: str,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    setting, items = _campaigns(db); campaign = _find(items, campaign_id); campaign["status"] = "PUBLISHED"; campaign["published_at"] = datetime.now(UTC).isoformat()
    setting.value = {"items": items}; db.add(setting); db.add(FlowEvent(module="MARKETING", action="CAMPAIGN_PUBLISHED", item_reference=campaign_id, actor=audit_actor("marketing"), result="SUCCESS", metadata_json={"slug": campaign["slug"], "tv_enabled": bool(campaign.get("tv_enabled", True))})); db.commit()
    return _with_clicks(db, [campaign])[0]


@admin_router.post("/campaigns/{campaign_id}/media")
async def upload_campaign_media(campaign_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, object]:
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "video/mp4": ".mp4", "video/webm": ".webm"}
    if file.content_type not in allowed: raise HTTPException(status_code=415, detail="Use JPG, PNG, WebP, MP4 o WebM")
    settings = get_settings(); raw = await file.read((settings.campaign_max_upload_mb * 1024 * 1024) + 1)
    if len(raw) > settings.campaign_max_upload_mb * 1024 * 1024: raise HTTPException(status_code=413, detail=f"El archivo supera {settings.campaign_max_upload_mb} MB")
    scan_bytes(raw, settings=settings)
    _validate_media(raw, file.content_type)
    setting, items = _campaigns(db); campaign = _find(items, campaign_id); digest = hashlib.sha256(raw).hexdigest()[:16]
    folder = settings.media_root / "campaigns"; folder.mkdir(parents=True, exist_ok=True); name = f"{campaign_id}-{digest}{allowed[file.content_type]}"; (folder / name).write_bytes(raw)
    campaign["media_url"] = f"{settings.public_media_base_url}/campaigns/{name}"; campaign["media_type"] = "VIDEO" if file.content_type.startswith("video/") else "IMAGE"
    setting.value = {"items": items}; db.add(setting); db.commit(); return _with_clicks(db, [campaign])[0]


@public_router.get("/api/v1/marketing/campaigns")
def public_campaigns(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    _, items = _campaigns(db)
    return [item for item in _with_clicks(db, items) if item.get("status") == "PUBLISHED" and _is_current(item)]


@public_router.get("/c/{slug}")
def track_campaign(slug: str, db: Session = Depends(get_db)) -> RedirectResponse:
    _, items = _campaigns(db); campaign = next((item for item in items if item.get("slug") == slug and item.get("status") == "PUBLISHED"), None)
    if campaign is None: raise HTTPException(status_code=404, detail="Campaña no encontrada")
    db.add(FlowEvent(module="MARKETING", action="CAMPAIGN_CLICK", item_reference=str(campaign["id"]), actor="visitante-web", result="SUCCESS", metadata_json={"slug": slug})); db.commit()
    return RedirectResponse(url=f"/lading?campaign={slug}", status_code=302)
