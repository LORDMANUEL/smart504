from __future__ import annotations

from datetime import UTC, datetime
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_admin
from app.db import get_db
from app.models import (
    Branch,
    DocumentRender,
    DocumentTemplate,
    DocumentTemplateVersion,
    FlowEvent,
)
from app.schemas import (
    DocumentRenderRead,
    DocumentTemplateCreate,
    DocumentTemplatePreview,
    DocumentTemplatePublish,
    DocumentTemplateRead,
    DocumentTemplateVersionCreate,
    DocumentTemplateVersionRead,
)
from app.services.document_templates import (
    SAMPLE_CONTEXT,
    extract_variables,
    render_source,
    validate_template_source,
)
from app.services.branding import branding_template_context, load_branding
from app.request_context import audit_actor, current_identity
from app.config import get_settings
from app.services.malware import scan_bytes

router = APIRouter(
    prefix="/api/v1/operations/documents",
    tags=["document-templates"],
    dependencies=[Depends(require_admin)],
)


def load_template(db: Session, template_id: str) -> DocumentTemplate:
    template = db.scalar(
        select(DocumentTemplate)
        .options(selectinload(DocumentTemplate.versions))
        .where(DocumentTemplate.id == template_id, DocumentTemplate.organization_id == current_identity().organization_id)
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@router.get("/templates", response_model=list[DocumentTemplateRead])
def list_templates(db: Session = Depends(get_db)) -> list[DocumentTemplate]:
    return list(
        db.scalars(
            select(DocumentTemplate)
            .options(selectinload(DocumentTemplate.versions))
            .where(DocumentTemplate.organization_id == current_identity().organization_id)
            .order_by(DocumentTemplate.document_type, DocumentTemplate.name)
        ).unique()
    )


@router.post("/templates", response_model=DocumentTemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(data: DocumentTemplateCreate, db: Session = Depends(get_db)) -> DocumentTemplate:
    validate_template_source(data.html_template, data.css_text)
    org = current_identity().organization_id
    if data.branch_id and db.scalar(select(Branch.id).where(Branch.id == data.branch_id, Branch.organization_id == org)) is None:
        raise HTTPException(status_code=422, detail="La sucursal indicada no existe")
    if db.scalar(select(DocumentTemplate.id).where(DocumentTemplate.organization_id == org, DocumentTemplate.code == data.code)):
        raise HTTPException(status_code=409, detail="Ya existe una plantilla con ese codigo")
    template = DocumentTemplate(
        organization_id=org,
        branch_id=data.branch_id,
        code=data.code,
        name=data.name,
        document_type=data.document_type,
        current_version=1,
    )
    version = DocumentTemplateVersion(
        organization_id=org,
        version=1,
        paper_size=data.paper_size,
        print_profile_json=data.print_profile.model_dump(mode="json"),
        html_template=data.html_template,
        css_text=data.css_text,
        variables_json=extract_variables(data.html_template),
        change_note=data.change_note or "Version inicial",
        created_by=audit_actor(data.created_by),
    )
    template.versions.append(version)
    db.add(template)
    db.add(FlowEvent(organization_id=org, module="DOCUMENTS", action="TEMPLATE_CREATED", item_reference=data.code,
                     actor=audit_actor(data.created_by), result="SUCCESS", metadata_json={"document_type": data.document_type, "version": 1}))
    db.commit()
    return load_template(db, template.id)


@router.post("/templates/import", response_model=DocumentTemplateRead, status_code=status.HTTP_201_CREATED)
async def import_template_files(
    code: str = Form(...),
    name: str = Form(...),
    document_type: str = Form(...),
    paper_size: str = Form("LETTER"),
    print_profile_json: str = Form("{}"),
    change_note: str = Form(...),
    template_id: str | None = Form(default=None),
    branch_id: str | None = Form(default=None),
    html_file: UploadFile = File(...),
    css_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> DocumentTemplate:
    if not (html_file.filename or "").lower().endswith((".html", ".htm")):
        raise HTTPException(status_code=422, detail="El formato principal debe ser un archivo .html")
    html_bytes = await html_file.read()
    css_bytes = await css_file.read() if css_file else b""
    if len(html_bytes) > 100_000 or len(css_bytes) > 30_000:
        raise HTTPException(status_code=413, detail="El formato excede el limite permitido")
    scan_bytes(html_bytes, settings=get_settings())
    if css_bytes:
        scan_bytes(css_bytes, settings=get_settings())
    try:
        html_text = html_bytes.decode("utf-8-sig")
        css_text = css_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Los archivos deben usar codificacion UTF-8") from exc
    if template_id:
        try:
            print_profile = json.loads(print_profile_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="La configuración de impresión no es válida") from exc
        template = load_template(db, template_id)
        payload = DocumentTemplateVersionCreate(
            paper_size=paper_size,
            print_profile=print_profile,
            html_template=html_text,
            css_text=css_text,
            change_note=change_note,
            created_by=audit_actor(),
        )
        create_version(template.id, payload, db)
        db.expire_all()
        return load_template(db, template.id)
    try:
        print_profile = json.loads(print_profile_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="La configuración de impresión no es válida") from exc
    payload = DocumentTemplateCreate(
        code=code.upper(), name=name, document_type=document_type, branch_id=branch_id or None,
        paper_size=paper_size, print_profile=print_profile, html_template=html_text, css_text=css_text,
        change_note=change_note, created_by=audit_actor(),
    )
    return create_template(payload, db)


@router.get("/templates/{template_id}/export")
def export_template_bundle(template_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    template = load_template(db, template_id)
    ordered = sorted(template.versions, key=lambda item: item.version, reverse=True)
    payload = {
        "format": "smartdiag504-document-template-v1",
        "template": {
            "organization_id": template.organization_id,
            "branch_id": template.branch_id,
            "code": template.code,
            "name": template.name,
            "document_type": template.document_type,
            "published_version": template.published_version,
        },
        "versions": [{
            "version": item.version,
            "status": item.status,
            "paper_size": item.paper_size,
            "print_profile": item.print_profile_json,
            "html_template": item.html_template,
            "css_text": item.css_text,
            "variables": item.variables_json,
            "change_note": item.change_note,
            "created_at": item.created_at,
        } for item in ordered],
    }
    return JSONResponse(jsonable_encoder(payload), headers={"Content-Disposition": f'attachment; filename="{template.code}.smartdiag.json"'})


@router.post("/templates/{template_id}/versions", response_model=DocumentTemplateVersionRead, status_code=status.HTTP_201_CREATED)
def create_version(template_id: str, data: DocumentTemplateVersionCreate, db: Session = Depends(get_db)) -> DocumentTemplateVersion:
    validate_template_source(data.html_template, data.css_text)
    template = load_template(db, template_id)
    next_version = template.current_version + 1
    version = DocumentTemplateVersion(
        organization_id=current_identity().organization_id,
        template_id=template.id,
        version=next_version,
        paper_size=data.paper_size,
        print_profile_json=data.print_profile.model_dump(mode="json"),
        html_template=data.html_template,
        css_text=data.css_text,
        variables_json=extract_variables(data.html_template),
        change_note=data.change_note,
        created_by=audit_actor(data.created_by),
    )
    template.current_version = next_version
    template.status = "DRAFT"
    db.add_all([template, version, FlowEvent(organization_id=current_identity().organization_id, module="DOCUMENTS", action="TEMPLATE_VERSION_CREATED",
        item_reference=template.code, actor=audit_actor(data.created_by), result="SUCCESS", metadata_json={"version": next_version})])
    db.commit()
    db.refresh(version)
    return version


@router.post("/templates/{template_id}/publish", response_model=DocumentTemplateRead)
def publish_template(template_id: str, data: DocumentTemplatePublish, db: Session = Depends(get_db)) -> DocumentTemplate:
    template = load_template(db, template_id)
    version = db.scalar(select(DocumentTemplateVersion).where(
        DocumentTemplateVersion.template_id == template.id,
        DocumentTemplateVersion.version == data.version,
    ))
    if version is None:
        raise HTTPException(status_code=404, detail="Version no encontrada")
    for previous in template.versions:
        if previous.status == "PUBLISHED":
            previous.status = "ARCHIVED"
    version.status = "PUBLISHED"
    version.published_at = datetime.now(UTC)
    template.published_version = version.version
    template.status = "PUBLISHED"
    db.add(FlowEvent(organization_id=current_identity().organization_id, module="DOCUMENTS", action="TEMPLATE_PUBLISHED", item_reference=template.code,
                     actor=audit_actor(data.actor), result="SUCCESS", metadata_json={"version": version.version}))
    db.commit()
    return load_template(db, template.id)


@router.post("/preview", response_class=HTMLResponse)
def preview_template(data: DocumentTemplatePreview, db: Session = Depends(get_db)) -> HTMLResponse:
    context = {**SAMPLE_CONTEXT, **branding_template_context(load_branding(db, current_identity().organization_id))}
    return HTMLResponse(render_source(data.html_template, data.css_text, data.paper_size, context, data.print_profile.model_dump(mode="json")))


@router.get("/renders", response_model=list[DocumentRenderRead])
def list_renders(reference: str | None = None, db: Session = Depends(get_db)) -> list[DocumentRender]:
    query = select(DocumentRender).where(DocumentRender.organization_id == current_identity().organization_id).order_by(DocumentRender.created_at.desc()).limit(100)
    if reference:
        query = query.where(DocumentRender.business_reference == reference)
    return list(db.scalars(query))
