from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Branch, DocumentTemplate, DocumentTemplateVersion, FlowEvent, ManagementDocument, WarehouseLocation, WorkshopSetting


ORGANIZATION = "SMARTDIAG504"
DOCUMENT_TYPES = {
    "QUOTE": ("Cotizacion", "Detalle de servicios y repuestos propuestos", "quote.rows_html"),
    "INVOICE": ("Factura preimpresa", "Comprobante para papel fiscal preimpreso", "quote.rows_html"),
    "DIAGNOSIS": ("Diagnostico tecnico", "Hallazgos, evidencia y recomendaciones", "evidence.rows_html"),
    "WORK_ORDER": ("Orden de trabajo", "Autorizacion y seguimiento del servicio", "evidence.rows_html"),
    "WARRANTY": ("Certificado de garantia", "Cobertura, condiciones y firmas", "evidence.rows_html"),
    "EXIT_PASS": ("Pase de salida", "Liberacion controlada del vehiculo", "evidence.rows_html"),
    "PICKING_TICKET": ("Ticket de picking", "Preparacion de repuestos por ubicacion", "warehouse.rows_html"),
    "WAREHOUSE_DELIVERY": ("Entrega de bodega", "Repuestos entregados y recibidos", "warehouse.rows_html"),
    "WAREHOUSE_RETURN": ("Devolucion a bodega", "Retorno y condicion de repuestos", "warehouse.rows_html"),
    "WAREHOUSE_RECEIPT": ("Entrada de mercancia", "Recepcion y control de inventario", "warehouse.rows_html"),
    "PAYSLIP": ("Voucher de pago", "Detalle de ingresos y deducciones", "evidence.rows_html"),
}

BASE_CSS = """
body{font-family:Arial,Helvetica,sans-serif;color:#17181c;font-size:10pt;line-height:1.45}
.document-header{display:flex;align-items:center;justify-content:space-between;border-bottom:4px solid {{ company.primary_color }};padding-bottom:10px;margin-bottom:18px}
.company-logo{max-width:168px;max-height:68px;object-fit:contain}.document-id{text-align:right}.document-id h1{font-size:20pt;margin:0;color:{{ company.primary_color }}}
.document-id strong{font-size:12pt}.company-data,.record-data{border:1px solid #d9dde5;border-radius:8px;padding:10px;margin:10px 0}.company-data{background:#f6f7f9}
.record-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px 20px}h2{font-size:12pt;color:{{ company.primary_color }};margin:16px 0 7px}
table{width:100%;border-collapse:collapse;margin-top:8px}th{background:#17181c;color:#fff;text-align:left;padding:8px}td{padding:8px;border-bottom:1px solid #d9dde5}
.totals{text-align:right;border-top:2px solid #17181c;margin-top:14px;padding-top:8px}.totals strong{font-size:15pt;color:{{ company.primary_color }}}
.signatures{display:flex;justify-content:space-between;gap:28px;margin-top:42px}.signature{width:45%;border-top:1px solid #17181c;text-align:center;padding-top:5px}
footer{border-top:1px solid #d9dde5;margin-top:26px;padding-top:8px;color:#626773;font-size:8pt;text-align:center}
"""


def body(title: str, description: str, rows_variable: str) -> str:
    return f"""<header class="document-header"><img class="company-logo" src="{{{{ company.logo_data_uri }}}}" alt="Logo SmartDiag504"><div class="document-id"><h1>{title}</h1><strong>{{{{ document.number }}}}</strong><br><small>{{{{ document.date }}}}</small></div></header>
<section class="company-data"><strong>{{{{ company.legal_name }}}}</strong><br>{{{{ company.address }}}} · {{{{ company.phone }}}}<br>RTN: {{{{ company.tax_id }}}} · {{{{ company.email }}}}</section>
<section class="record-data"><div class="record-grid"><span><b>Cliente:</b> {{{{ customer.name }}}}</span><span><b>Telefono:</b> {{{{ customer.phone }}}}</span><span><b>Vehiculo:</b> {{{{ vehicle.label }}}}</span><span><b>VIN:</b> {{{{ vehicle.vin }}}}</span><span><b>OT:</b> {{{{ work_order.number }}}}</span><span><b>Estado:</b> {{{{ work_order.status }}}}</span></div></section>
<h2>{description}</h2><p>{{{{ work_order.diagnosis }}}}</p>
<table><thead><tr><th>Codigo / concepto</th><th>Descripcion</th><th>Cantidad</th><th>Valor / estado</th></tr></thead><tbody>{{{{ {rows_variable} }}}}</tbody></table>
<section class="totals"><span>Total</span><br><strong>{{{{ quote.total }}}}</strong></section>
<section class="signatures"><div class="signature">Responsable SmartDiag504</div><div class="signature">Cliente / recibe conforme</div></section>
<footer>{{{{ company.document_footer }}}}<br>Documento generado y conservado por SmartDiag504.</footer>"""


def ensure_branch_and_warehouses(db) -> Branch:
    branch = db.scalar(select(Branch).where(Branch.organization_id == ORGANIZATION, Branch.code == "MAIN"))
    if branch is None:
        branch = Branch(organization_id=ORGANIZATION, code="MAIN", name="SmartDiag504 - Taller principal", address="Tegucigalpa, Honduras", phone="+504 0000-0000", email_domain="smartdiag504.com", active=True)
        db.add(branch); db.flush()
    else:
        branch.active = True
    for code, name, warehouse_type in (
        ("MAIN-STOCK", "Bodega principal", "STOCK"),
        ("MAIN-PROCESS", "Repuestos reservados / proceso", "PROCESS"),
        ("MAIN-TRANSIT", "Bodega en transito", "TRANSIT"),
        ("MAIN-RETURNS", "Bodega de devoluciones", "RETURNS"),
    ):
        if db.scalar(select(WarehouseLocation.id).where(WarehouseLocation.organization_id == ORGANIZATION, WarehouseLocation.code == code)) is None:
            db.add(WarehouseLocation(organization_id=ORGANIZATION, branch_id=branch.id, code=code, name=name, warehouse_type=warehouse_type, active=True))
    return branch


def ensure_templates(db) -> int:
    created = 0
    profiles = (
        ("BRANDED", "Membrete SmartDiag504", {"printer_type":"LASER_INKJET","orientation":"PORTRAIT","margins_mm":{"top":10,"right":10,"bottom":10,"left":10},"copies":1,"show_logo":True,"preprinted_background":False}),
        ("PREPRINTED", "Papel preimpreso", {"printer_type":"PREPRINTED","orientation":"PORTRAIT","margins_mm":{"top":18,"right":12,"bottom":12,"left":12},"copies":2,"show_logo":False,"preprinted_background":True}),
        ("PDF", "Archivo PDF", {"printer_type":"BROWSER_PDF","orientation":"PORTRAIT","margins_mm":{"top":10,"right":10,"bottom":10,"left":10},"copies":1,"show_logo":True,"preprinted_background":False}),
    )
    for document_type, (title, description, rows_variable) in DOCUMENT_TYPES.items():
        for suffix, profile_name, profile in profiles:
            code = f"SD504_{document_type}_{suffix}"
            template = db.scalar(select(DocumentTemplate).where(DocumentTemplate.organization_id == ORGANIZATION, DocumentTemplate.code == code))
            if template is not None:
                continue
            is_default = suffix == ("PREPRINTED" if document_type == "INVOICE" else "BRANDED")
            template = DocumentTemplate(organization_id=ORGANIZATION, branch_id=None, code=code, name=f"{title} · {profile_name}", document_type=document_type, status="PUBLISHED" if is_default else "DRAFT", current_version=1, published_version=1 if is_default else None, active=True)
            template.versions.append(DocumentTemplateVersion(organization_id=ORGANIZATION, version=1, status="PUBLISHED" if is_default else "DRAFT", paper_size="LETTER", print_profile_json=profile, html_template=body(title, description, rows_variable), css_text=BASE_CSS, variables_json=[], change_note="Formato inicial SmartDiag504 para Epson L3250, PDF o papel preimpreso", created_by="bootstrap-production", published_at=datetime.now(UTC) if is_default else None))
            db.add(template); created += 1
    return created


def ensure_operational_settings(db, branch: Branch) -> None:
    values = {
        "production_hardware": {"printer_model":"Epson EcoTank L3250","printer_mode":"BROWSER_PDF_LETTER","pos_mode":"BANK_TERMINAL_EXTERNAL","pos_reference_required":True,"card_data_storage":False,"invoice_mode":"PREPRINTED"},
        "backup_policy": {"mode":"LOCAL_VPS_SNAPSHOT","retention_days":14,"risk_accepted":True,"note":"No protege contra perdida total del VPS"},
    }
    for key, value in values.items():
        setting = db.get(WorkshopSetting, key)
        if setting is None: db.add(WorkshopSetting(key=key, value=value))
        else: setting.value = value
    existing = db.scalar(select(ManagementDocument).where(ManagementDocument.organization_id == ORGANIZATION, ManagementDocument.branch_id == branch.id, ManagementDocument.document_type == "FISCAL_CONFIGURATION"))
    if existing is None:
        db.add(ManagementDocument(organization_id=ORGANIZATION, branch_id=branch.id, document_type="FISCAL_CONFIGURATION", number="FACTURA-PREIMPRESA", status="ACTIVE", metadata_json={"mode":"PREPRINTED","printer":"Epson EcoTank L3250","auto_print":False,"requires_manual_fiscal_control":True}))


def main() -> int:
    with SessionLocal() as db:
        branch = ensure_branch_and_warehouses(db)
        templates = ensure_templates(db)
        ensure_operational_settings(db, branch)
        db.add(FlowEvent(organization_id=ORGANIZATION, module="CONFIGURATION", action="PRODUCTION_DEFAULTS_BOOTSTRAPPED", item_reference=branch.code, actor="bootstrap-production", result="SUCCESS", metadata_json={"templates_created":templates,"printer":"Epson EcoTank L3250","invoice_mode":"PREPRINTED"}))
        db.commit()
    print(f"SmartDiag504 production defaults ready; templates_created={templates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
