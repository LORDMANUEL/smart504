from __future__ import annotations

import hashlib
from io import BytesIO

import boto3
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.config import get_settings
from app.db import get_db
from app.models import Branch, DocumentTemplate, FlowEvent, ManagementDocument, WorkshopSetting
from app.request_context import audit_actor, current_identity
from app.schemas import BrandingProfileRead, BrandingProfileUpdate, WorkshopSettingsRead, WorkshopSettingsUpdate
from app.services.branding import load_branding, record_asset_version, save_branding
from app.services.malware import scan_bytes

public_router = APIRouter(prefix="/api/v1", tags=["branding"])

router = APIRouter(
    prefix="/api/v1/operations/settings",
    tags=["settings"],
    dependencies=[Depends(require_admin)],
)

_DEFAULT = {"default_view": "KANBAN", "bays_enabled": False, "bay_codes": []}


@router.get("/production-readiness")
def production_readiness(db: Session = Depends(get_db)) -> dict[str, object]:
    """Administrative go-live gates; values never expose credentials."""
    identity = current_identity()
    settings = get_settings()
    organization_id = identity.organization_id
    active_branches = db.scalar(select(func.count()).select_from(Branch).where(
        Branch.organization_id == organization_id, Branch.active.is_(True)
    )) or 0
    fiscal_documents = db.scalar(select(func.count()).select_from(ManagementDocument).where(
        ManagementDocument.organization_id == organization_id,
        ManagementDocument.document_type == "CAI",
        ManagementDocument.status == "ACTIVE",
    )) or 0
    published_templates = db.scalar(select(func.count()).select_from(DocumentTemplate).where(
        DocumentTemplate.organization_id == organization_id,
        DocumentTemplate.active.is_(True),
        DocumentTemplate.published_version.is_not(None),
    )) or 0
    cashier_code = settings.cashier_access_code.get_secret_value() if settings.cashier_access_code else ""
    gates = [
        {"code": "ERP", "label": "ERPNext obligatorio y fiscal estricto", "ready": settings.frappe_required and settings.invoice_verification_mode == "strict", "owner": "SISTEMA"},
        {"code": "TENANT", "label": "Empresa con sucursal activa", "ready": active_branches > 0, "owner": "ADMINISTRADOR"},
        {"code": "CASHIER_SECRET", "label": "Código privado de caja en secretos", "ready": len(cashier_code) >= 6 and cashier_code != "5040", "owner": "ADMINISTRADOR"},
        {"code": "DOCUMENTS", "label": "Plantillas de impresión publicadas", "ready": published_templates >= 2, "owner": "ADMINISTRADOR"},
        {"code": "FISCAL", "label": "CAI/rangos aceptados por contador", "ready": fiscal_documents > 0, "owner": "CONTADOR"},
        {"code": "SMTP", "label": "Correo transaccional SMTP", "ready": bool(settings.smtp_host and settings.smtp_from_email), "owner": "PROVEEDOR"},
        {"code": "PRIVATE_STORAGE", "label": "Evidencias en almacenamiento S3 privado", "ready": settings.private_evidence_backend.lower() == "s3", "owner": "INFRAESTRUCTURA"},
        {"code": "MALWARE_SCAN", "label": "Escaneo antimalware obligatorio para archivos", "ready": settings.malware_scanner_required and bool(settings.malware_scanner_host), "owner": "SEGURIDAD"},
        {"code": "FISCAL_HARDWARE", "label": "Impresora/POS fiscal aceptado", "ready": settings.fiscal_hardware_certified, "owner": "CONTADOR/HARDWARE"},
        {"code": "OFFSITE_BACKUP", "label": "Respaldo externo y restauración probada", "ready": settings.external_backup_configured and settings.offsite_restore_tested, "owner": "INFRAESTRUCTURA"},
    ]
    return {
        "environment": settings.environment,
        "organization_id": organization_id,
        "production_ready": all(bool(item["ready"]) for item in gates),
        "gates": gates,
        "summary": {"ready": sum(bool(item["ready"]) for item in gates), "total": len(gates)},
    }


@public_router.get("/branding", response_model=BrandingProfileRead)
def public_branding(db: Session = Depends(get_db)) -> dict[str, object]:
    profile = load_branding(db)
    profile["asset_history"] = []
    return profile


@router.get("/workshop", response_model=WorkshopSettingsRead)
def get_workshop_settings(db: Session = Depends(get_db)) -> WorkshopSettingsRead:
    setting = db.get(WorkshopSetting, "workshop_ui")
    value = setting.value if setting else _DEFAULT
    return WorkshopSettingsRead.model_validate(value)


@router.put("/workshop", response_model=WorkshopSettingsRead)
def update_workshop_settings(
    data: WorkshopSettingsUpdate,
    db: Session = Depends(get_db),
) -> WorkshopSettingsRead:
    if data.default_view == "BAYS" and not data.bays_enabled:
        data = data.model_copy(update={"default_view": "KANBAN"})
    setting = db.get(WorkshopSetting, "workshop_ui")
    if setting is None:
        setting = WorkshopSetting(key="workshop_ui", value=data.model_dump())
        db.add(setting)
    else:
        setting.value = data.model_dump()
    db.commit()
    return WorkshopSettingsRead.model_validate(setting.value)


@router.get("/branding", response_model=BrandingProfileRead)
def get_branding(db: Session = Depends(get_db)) -> dict[str, object]:
    return load_branding(db, current_identity().organization_id)


@router.put("/branding", response_model=BrandingProfileRead)
def update_branding(
    data: BrandingProfileUpdate,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    organization_id = current_identity().organization_id
    profile = save_branding(db, organization_id, data.model_dump(mode="json"))
    db.add(FlowEvent(
        organization_id=organization_id,
        module="SETTINGS",
        action="BRANDING_UPDATED",
        item_reference=organization_id,
        actor=audit_actor(),
        result="SUCCESS",
        metadata_json={"primary_color": data.primary_color, "display_name": data.display_name},
    ))
    db.commit()
    return load_branding(db, organization_id)


@router.post("/branding/assets", response_model=BrandingProfileRead, status_code=status.HTTP_201_CREATED)
async def upload_brand_asset(
    asset_type: str = Form(..., pattern=r"^(LOGO|LOGO_DARK|FAVICON)$"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    allowed = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Use PNG, JPG o WebP para la marca")
    raw = await file.read(4 * 1024 * 1024 + 1)
    await file.close()
    if not raw:
        raise HTTPException(status_code=422, detail="El archivo de marca esta vacio")
    if len(raw) > 4 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo de marca supera 4 MB")
    scan_bytes(raw, settings=get_settings())
    try:
        with Image.open(BytesIO(raw)) as image:
            image.verify()
        with Image.open(BytesIO(raw)) as image:
            width, height = image.size
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise HTTPException(status_code=422, detail="El archivo no es una imagen valida") from exc
    if width < 32 or height < 32 or width > 6000 or height > 6000:
        raise HTTPException(status_code=422, detail="La imagen debe medir entre 32 y 6000 pixeles por lado")

    organization_id = current_identity().organization_id
    settings = get_settings()
    digest = hashlib.sha256(raw).hexdigest()
    extension = allowed[file.content_type]
    object_key = f"branding/{organization_id}/{asset_type.lower()}-{digest[:20]}{extension}"
    if settings.media_backend.lower() == "s3":
        if not settings.s3_endpoint_url or not settings.s3_access_key_id or not settings.s3_secret_access_key:
            raise HTTPException(status_code=503, detail="El almacenamiento S3 no esta configurado")
        client = boto3.client(
            "s3", endpoint_url=settings.s3_endpoint_url, region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
        )
        client.put_object(Bucket=settings.s3_bucket, Key=object_key, Body=raw, ContentType=file.content_type,
                          Metadata={"sha256": digest, "asset-type": asset_type})
    else:
        path = settings.media_root / object_key
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(raw)
        temporary.replace(path)

    public_url = f"{settings.public_media_base_url.rstrip('/')}/{object_key}"
    field = {"LOGO": "logo_url", "LOGO_DARK": "logo_dark_url", "FAVICON": "favicon_url"}[asset_type]
    current = load_branding(db, organization_id)
    save_branding(db, organization_id, {
        field: public_url,
        "asset_history": record_asset_version(current, asset_type=asset_type, url=public_url, actor=audit_actor()),
    })
    db.add(FlowEvent(
        organization_id=organization_id,
        module="SETTINGS",
        action="BRAND_ASSET_REPLACED",
        item_reference=asset_type,
        actor=audit_actor(),
        result="SUCCESS",
        metadata_json={"url": public_url, "sha256": digest, "width": width, "height": height},
    ))
    db.commit()
    return load_branding(db, organization_id)
