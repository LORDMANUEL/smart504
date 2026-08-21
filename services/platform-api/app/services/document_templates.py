from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from html import escape
from html.parser import HTMLParser
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import DocumentRender, DocumentTemplate, DocumentTemplateVersion
from app.request_context import current_identity
from app.services.branding import branding_template_context, load_branding

VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_.]+)\s*}}")
FORBIDDEN_PATTERNS = (
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"\son[a-z]+\s*=", re.IGNORECASE),
    re.compile(r"<\s*(iframe|object|embed|form|input|button)", re.IGNORECASE),
    re.compile(r"@import", re.IGNORECASE),
    re.compile(r"url\s*\(\s*['\"]?https?://", re.IGNORECASE),
)

ALLOWED_TEMPLATE_TAGS = {
    "html", "head", "meta", "title", "style", "body", "header", "footer", "main",
    "section", "article", "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "ul", "ol", "li", "dl",
    "dt", "dd", "strong", "b", "em", "i", "small", "br", "hr", "img",
}
ALLOWED_TEMPLATE_ATTRIBUTES = {
    "class", "id", "style", "colspan", "rowspan", "scope", "alt", "width", "height", "src",
    "charset", "name", "content",
}
UNSAFE_RESOURCE_PATTERN = re.compile(
    r"(?:url\s*\(|@import|expression\s*\(|behavior\s*:|-moz-binding|(?:https?|ftp|file|data:text)\s*:|//)",
    re.IGNORECASE,
)


class _TemplateAllowlistParser(HTMLParser):
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if normalized_tag not in ALLOWED_TEMPLATE_TAGS:
            raise ValueError(f"Etiqueta no permitida: {normalized_tag}")
        for name, value in attrs:
            normalized_name = name.lower()
            if normalized_name not in ALLOWED_TEMPLATE_ATTRIBUTES or normalized_name.startswith("on"):
                raise ValueError(f"Atributo no permitido: {normalized_name}")
            text = value or ""
            if normalized_name == "src":
                if normalized_tag != "img" or not (
                    text == "{{ company.logo_data_uri }}"
                    or re.fullmatch(r"data:image/(?:png|jpeg|webp);base64,[A-Za-z0-9+/=\s]+", text)
                ):
                    raise ValueError("Sólo se permiten imágenes incrustadas y verificadas")
            if normalized_name == "style" and UNSAFE_RESOURCE_PATTERN.search(text):
                raise ValueError("El estilo intenta cargar un recurso externo")

    handle_startendtag = handle_starttag

PAPER_CSS = {
    "LETTER": "@page { size: letter; margin: 18mm; }",
    "A4": "@page { size: A4; margin: 16mm; }",
    "THERMAL_80": "@page { size: 80mm auto; margin: 4mm; } body { width: 72mm; }",
    "THERMAL_58": "@page { size: 58mm auto; margin: 3mm; } body { width: 52mm; }",
}

SAMPLE_CONTEXT: dict[str, Any] = {
    "company.name": "SmartDiag504",
    "company.legal_name": "Taller de demostracion SmartDiag504",
    "company.tax_id": "RTN-DEMO-504",
    "company.address": "Tegucigalpa, Honduras",
    "company.phone": "+504 0000-0000",
    "company.email": "info@smartdiag504.com",
    "company.website": "https://taller.nexusmedi.org",
    "company.logo_url": "/brand/smartdiag504-logo.png",
    "company.logo_dark_url": "/brand/smartdiag504-logo.png",
    "company.logo_data_uri": "",
    "company.primary_color": "#ED111C",
    "company.accent_color": "#C3000B",
    "company.document_footer": "Documento generado desde SmartDiag504.",
    "document.number": "DOC-DEMO-0001",
    "document.date": "13/08/2026",
    "document.title": "Documento de demostracion",
    "customer.name": "Cliente de demostracion",
    "customer.phone": "+504 9999-9999",
    "vehicle.label": "Ford Escape 2020",
    "vehicle.vin": "1FMCU0G6XLUA12545",
    "work_order.number": "OT-DEMO-001",
    "work_order.status": "EN PROCESO",
    "work_order.diagnosis": "Revision preventiva y diagnostico electronico.",
    "quote.subtotal": "L 4,000.00",
    "quote.discount": "L 0.00",
    "quote.tax": "L 600.00",
    "quote.total": "L 4,600.00",
    "quote.rows_html": "<tr><td>MO-001</td><td>Diagnostico electronico</td><td>1</td><td>L 4,000.00</td></tr>",
    "evidence.rows_html": "<tr><td>Diagnostico</td><td>Conector revisado</td><td>Tecnico demo</td></tr>",
    "document.notes": "Documento generado desde SmartDiag504.",
}

TRUSTED_HTML_VARIABLES = {"quote.rows_html", "evidence.rows_html", "warehouse.rows_html"}
CSS_VARIABLES = {"company.primary_color", "company.accent_color"}


def brand_fallback_html(fallback_html: str, context: dict[str, Any]) -> str:
    """Apply the tenant brand to legacy fallback documents without mutating history."""
    display_name = escape(str(context.get("company.name", "SmartDiag504")))
    footer = escape(str(context.get("company.document_footer", "")))
    primary = str(context.get("company.primary_color", "#ED111C"))
    accent = str(context.get("company.accent_color", "#C3000B"))
    branded = fallback_html.replace("SMARTDIAG504", display_name).replace("SmartDiag504", display_name)
    branded = branded.replace("#ed111c", primary).replace("#ED111C", primary)
    branded = branded.replace("#c3000b", accent).replace("#C3000B", accent)
    branded = branded.replace("Documento generado desde SmartDiag504.", footer)
    logo_data_uri = str(context.get("company.logo_data_uri", ""))
    if logo_data_uri and "brand-document-logo" not in branded:
        logo = (
            '<img class="brand-document-logo" alt="" '
            f'src="{escape(logo_data_uri)}" style="max-width:180px;max-height:72px;object-fit:contain">'
        )
        branded = re.sub(r"(<body[^>]*>)", rf"\1{logo}", branded, count=1, flags=re.IGNORECASE)
    return branded


def extract_variables(html_template: str) -> list[str]:
    return sorted(set(VARIABLE_PATTERN.findall(html_template)))


def validate_template_source(html_template: str, css_text: str) -> None:
    combined = f"{html_template}\n{css_text}"
    if any(pattern.search(combined) for pattern in FORBIDDEN_PATTERNS):
        raise HTTPException(
            status_code=422,
            detail="La plantilla contiene scripts, eventos o recursos externos no permitidos",
        )
    if UNSAFE_RESOURCE_PATTERN.search(css_text):
        raise HTTPException(status_code=422, detail="La plantilla intenta cargar recursos externos")
    try:
        parser = _TemplateAllowlistParser(convert_charrefs=True)
        parser.feed(html_template)
        parser.close()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def render_source(
    html_template: str,
    css_text: str,
    paper_size: str,
    context: dict[str, Any],
    print_profile: dict[str, object] | None = None,
) -> str:
    validate_template_source(html_template, css_text)

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = context.get(key, "")
        if key in TRUSTED_HTML_VARIABLES:
            return str(value)
        return escape(str(value))

    body = VARIABLE_PATTERN.sub(replace, html_template)
    rendered_css = VARIABLE_PATTERN.sub(
        lambda match: str(context.get(match.group(1), ""))
        if match.group(1) in CSS_VARIABLES
        else "",
        css_text,
    )
    page_css = PAPER_CSS.get(paper_size, PAPER_CSS["LETTER"])
    profile = print_profile or {}
    orientation = "landscape" if profile.get("orientation") == "LANDSCAPE" else "portrait"
    margins = profile.get("margins_mm") if isinstance(profile.get("margins_mm"), dict) else {}
    margin_css = " ".join(f"{max(0, min(50, float(margins.get(side, 10))))}mm" for side in ("top", "right", "bottom", "left"))
    page_css += f"@page{{size:{'auto' if paper_size.startswith('THERMAL') else paper_size.lower()} {orientation};margin:{margin_css}}}"
    if profile.get("show_logo") is False:
        page_css += ".company-logo{display:none!important}"
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        f"<style>{page_css}{rendered_css}</style></head><body>{body}</body></html>"
    )


def published_template(
    db: Session,
    document_type: str,
    organization_id: str = "SMARTDIAG504",
    branch_id: str | None = None,
) -> tuple[DocumentTemplate, DocumentTemplateVersion] | None:
    query = select(DocumentTemplate).where(
        DocumentTemplate.organization_id == organization_id,
        DocumentTemplate.document_type == document_type,
        DocumentTemplate.active.is_(True),
        DocumentTemplate.published_version.is_not(None),
    )
    if branch_id:
        query = query.where(
            or_(
                DocumentTemplate.branch_id == branch_id,
                DocumentTemplate.branch_id.is_(None),
            )
        ).order_by(
            DocumentTemplate.branch_id.desc().nullslast(), DocumentTemplate.updated_at.desc()
        )
    else:
        query = query.where(DocumentTemplate.branch_id.is_(None)).order_by(
            DocumentTemplate.updated_at.desc()
        )
    template = db.scalar(query.limit(1))
    if template is None or template.published_version is None:
        return None
    version = db.scalar(
        select(DocumentTemplateVersion).where(
            DocumentTemplateVersion.template_id == template.id,
            DocumentTemplateVersion.version == template.published_version,
        )
    )
    return (template, version) if version else None


def render_published_or_fallback(
    db: Session,
    document_type: str,
    context: dict[str, Any],
    fallback_html: str,
    branch_id: str | None = None,
) -> tuple[str, DocumentTemplate | None, DocumentTemplateVersion | None]:
    organization_id = current_identity().organization_id
    branded_context = {**context, **branding_template_context(load_branding(db, organization_id))}
    selected = published_template(db, document_type, organization_id=organization_id, branch_id=branch_id)
    if not selected:
        return brand_fallback_html(fallback_html, branded_context), None, None
    template, version = selected
    return (
        render_source(version.html_template, version.css_text, version.paper_size, branded_context, version.print_profile_json),
        template,
        version,
    )


def persist_render(
    db: Session,
    document_type: str,
    business_reference: str,
    html_snapshot: str,
    actor: str,
    template: DocumentTemplate | None = None,
    version: DocumentTemplateVersion | None = None,
    branch_id: str | None = None,
) -> DocumentRender:
    render = DocumentRender(
        branch_id=branch_id,
        template_id=template.id if template else None,
        template_version_id=version.id if version else None,
        document_type=document_type,
        business_reference=business_reference,
        html_snapshot=html_snapshot,
        content_sha256=hashlib.sha256(html_snapshot.encode("utf-8")).hexdigest(),
        created_by=actor,
        created_at=datetime.now(UTC),
    )
    db.add(render)
    db.flush()
    return render
