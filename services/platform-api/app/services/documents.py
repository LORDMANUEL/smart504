from __future__ import annotations

from html import escape
from io import BytesIO
import base64

from xhtml2pdf import pisa

from app.models import Quote, WorkOrder
from app.config import get_settings


def _evidence_image(item: dict[str, object], work_order_id: str) -> str:
    storage_key = str(item.get("storage_key") or "")
    mime_type = str(item.get("mime_type") or "")
    if not storage_key or "/" in storage_key or "\\" in storage_key:
        return ""
    path = get_settings().private_evidence_root / work_order_id / storage_key
    if not path.is_file() or mime_type not in {"image/jpeg", "image/png", "image/webp"}:
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        f'<img class="evidence-photo" src="data:{mime_type};base64,{encoded}" '
        f'alt="{escape(str(item.get("caption") or "Evidencia de diagnostico"))}">'
    )


def quote_template_context(quote: Quote, work_order: WorkOrder) -> dict[str, object]:
    rows = "".join(
        f"<tr><td>{escape(line.code)}</td><td>{escape(line.description)}</td>"
        f"<td>{line.quantity}</td><td>L {line.unit_price:,.2f}</td><td>L {line.line_total:,.2f}</td>"
        f"<td>{escape(line.approval_status)}</td></tr>" for line in quote.lines
    )
    return {
        "company.name": "SmartDiag504",
        "company.legal_name": "SmartDiag504",
        "company.tax_id": "",
        "company.address": "Tegucigalpa, Honduras",
        "company.phone": "",
        "document.number": quote.number,
        "document.date": quote.created_at.strftime("%d/%m/%Y") if quote.created_at else "",
        "document.title": "Cotizacion",
        "customer.name": work_order.customer_name,
        "customer.phone": "",
        "vehicle.label": work_order.vehicle_label,
        "vehicle.vin": "",
        "work_order.number": work_order.number,
        "work_order.status": work_order.status if hasattr(work_order, "status") else "PRE-OT",
        "work_order.diagnosis": getattr(work_order, "diagnosis", "") or "",
        "quote.subtotal": f"L {quote.subtotal:,.2f}",
        "quote.discount": f"L {quote.discount:,.2f}",
        "quote.tax": f"L {quote.tax:,.2f}",
        "quote.total": f"L {quote.total:,.2f}",
        "quote.rows_html": rows,
        "document.notes": quote.notes or "Cotizacion sujeta a disponibilidad y aprobacion del cliente.",
    }


def work_order_template_context(work_order: WorkOrder, title: str) -> dict[str, object]:
    evidence = [event.payload for event in work_order.events if event.event_type == "DIAGNOSTIC_EVIDENCE_ADDED"]
    evidence_rows = "".join(
        f"<tr><td>{escape(str(item.get('category', 'EVIDENCIA')))}</td>"
        f"<td>{escape(str(item.get('caption', '')))}</td><td>{escape(str(item.get('actor', '')))}</td></tr>"
        for item in evidence
    )
    return {
        "company.name": "SmartDiag504",
        "company.legal_name": "SmartDiag504",
        "company.tax_id": "",
        "company.address": "Tegucigalpa, Honduras",
        "company.phone": "",
        "document.number": work_order.number,
        "document.date": work_order.updated_at.strftime("%d/%m/%Y") if work_order.updated_at else "",
        "document.title": title,
        "customer.name": work_order.customer_name,
        "customer.phone": "",
        "vehicle.label": work_order.vehicle_label,
        "vehicle.vin": "",
        "work_order.number": work_order.number,
        "work_order.status": work_order.status,
        "work_order.diagnosis": work_order.diagnosis or "Sin observaciones adicionales",
        "evidence.rows_html": evidence_rows,
        "document.notes": "Documento generado desde la trazabilidad registrada en SmartDiag504.",
    }


def warehouse_template_context(work_order: WorkOrder, title: str) -> dict[str, object]:
    rows = "".join(
        f"<tr><td>{escape(str(part.get('sku', '')))}</td><td>{escape(str(part.get('name', '')))}</td>"
        f"<td>{escape(str(part.get('quantity', '')))}</td><td>{escape(str(part.get('location', '')))}</td>"
        f"<td>{escape(str(part.get('status', '')))}</td></tr>" for part in (work_order.parts_required or [])
    )
    context = work_order_template_context(work_order, title)
    context["warehouse.rows_html"] = rows
    return context


def quote_html(quote: Quote, work_order: WorkOrder) -> str:
    """Build the canonical printable HTML used by both browser print and PDF export."""
    rows = "".join(
        f"""<tr><td>{escape(line.code)}</td><td>{escape(line.description)}</td>
        <td class=\"num\">{line.quantity}</td><td class=\"num\">L {line.unit_price:,.2f}</td>
        <td class=\"num\">L {line.line_total:,.2f}</td><td>{escape(line.approval_status)}</td></tr>"""
        for line in quote.lines
    )
    return f"""<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">
    <title>{escape(quote.number)}</title><style>
    @page {{ size: letter; margin: 18mm; }} body {{ font-family: Helvetica, Arial, sans-serif; color:#17181c; font-size:10pt; }}
    header {{ border-bottom:3px solid #ed111c; padding-bottom:12px; margin-bottom:22px; }} h1 {{ margin:0; font-size:22pt; }}
    h2 {{ margin:5px 0 0; font-size:13pt; color:#ed111c; }} .meta {{ margin:14px 0 20px; line-height:1.7; }}
    table {{ width:100%; border-collapse:collapse; }} th {{ background:#17181c; color:white; padding:8px; text-align:left; }}
    td {{ border-bottom:1px solid #d9dde4; padding:8px; vertical-align:top; }} .num {{ text-align:right; white-space:nowrap; }}
    .totals {{ width:42%; margin:20px 0 0 auto; }} .totals div {{ display:flex; justify-content:space-between; padding:5px 0; }}
    .grand {{ border-top:2px solid #17181c; font-size:14pt; font-weight:bold; }} footer {{ margin-top:34px; color:#626874; font-size:8pt; }}
    </style></head><body><header><h1>SMARTDIAG504</h1><h2>Cotizaci&oacute;n {escape(quote.number)}</h2></header>
    <div class=\"meta\"><strong>OT:</strong> {escape(work_order.number)}<br><strong>Cliente:</strong> {escape(work_order.customer_name)}<br>
    <strong>Veh&iacute;culo:</strong> {escape(work_order.vehicle_label)}<br><strong>Estado:</strong> {escape(quote.status)}</div>
    <table><thead><tr><th>C&oacute;digo</th><th>Descripci&oacute;n</th><th>Cant.</th><th>Precio</th><th>Total</th><th>Aprobaci&oacute;n</th></tr></thead>
    <tbody>{rows}</tbody></table><section class=\"totals\"><div><span>Subtotal</span><b>L {quote.subtotal:,.2f}</b></div>
    <div><span>Descuento</span><b>L {quote.discount:,.2f}</b></div><div><span>Impuesto</span><b>L {quote.tax:,.2f}</b></div>
    <div class=\"grand\"><span>Total</span><b>L {quote.total:,.2f}</b></div></section>
    <footer>{escape(quote.notes or 'Cotizaci&oacute;n sujeta a disponibilidad y aprobaci&oacute;n del cliente.')}</footer></body></html>"""


def html_to_pdf(html: str) -> BytesIO:
    def deny_external_resource(uri: str, _relative_to: str) -> str:
        if uri.startswith("data:image/"):
            return uri
        raise RuntimeError("Los documentos no pueden cargar archivos o recursos externos")

    output = BytesIO()
    result = pisa.CreatePDF(html, dest=output, encoding="utf-8", link_callback=deny_external_resource)
    if result.err:
        raise RuntimeError("No se pudo convertir el documento HTML a PDF")
    output.seek(0)
    return output


def _legacy_work_order_document_html(work_order: WorkOrder, kind: str) -> str:
    titles = {"invoice": "Factura / comprobante de cobro", "warranty": "Certificado de garantía", "exit-pass": "Pase de salida del vehículo"}
    title = titles[kind]
    return f"""<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><title>{escape(title)}</title>
    <style>@page{{size:letter;margin:20mm}}body{{font-family:Helvetica;color:#17181c}}header{{border-bottom:3px solid #ed111c;padding-bottom:14px}}
    h1{{margin:0}}h2{{color:#ed111c}}dl{{margin-top:30px}}dt{{font-size:9pt;color:#666}}dd{{margin:4px 0 18px;font-weight:bold}}
    .sign{{margin-top:70px;display:flex;justify-content:space-between}}.sign span{{width:42%;border-top:1px solid #333;padding-top:7px;text-align:center}}</style></head>
    <body><header><h1>SMARTDIAG504</h1><h2>{escape(title)}</h2></header><dl><dt>Orden de trabajo</dt><dd>{escape(work_order.number)}</dd>
    <dt>Cliente</dt><dd>{escape(work_order.customer_name)}</dd><dt>Vehículo</dt><dd>{escape(work_order.vehicle_label)}</dd>
    <dt>Estado</dt><dd>{escape(work_order.status)}</dd><dt>Diagnóstico</dt><dd>{escape(work_order.diagnosis or 'Sin observaciones adicionales')}</dd></dl>
    <p>Documento generado desde la trazabilidad registrada en SmartDiag504.</p><div class=\"sign\"><span>Responsable del taller</span><span>Firma del cliente</span></div></body></html>"""


def work_order_document_html(work_order: WorkOrder, kind: str) -> str:
    titles = {
        "invoice": "Factura / comprobante de cobro",
        "warranty": "Certificado de garantia",
        "exit-pass": "Pase de salida del vehiculo",
        "diagnosis": "Informe de diagnostico con evidencia",
    }
    title = titles[kind]
    evidence = [event.payload for event in work_order.events if event.event_type == "DIAGNOSTIC_EVIDENCE_ADDED"]
    rows = "".join(
        f'<tr><td>{escape(str(item.get("category", "EVIDENCIA")))}</td><td>{escape(str(item.get("caption", "")))}</td>'
        f'<td>{escape(str(item.get("actor", "")))}</td><td>{escape(str(item.get("created_at", "")))}</td>'
        f'<td>{_evidence_image(item, work_order.id)}</td></tr>'
        for item in evidence
    )
    evidence_section = ""
    if kind == "diagnosis":
        evidence_section = (
            f'<h2>Evidencia fotografica registrada</h2><table><thead><tr><th>Tipo</th><th>Descripcion</th>'
            f'<th>Tecnico</th><th>Fecha</th><th>Foto</th></tr></thead><tbody>{rows}</tbody></table>'
            if rows else "<p>El tecnico todavia no ha adjuntado evidencia fotografica.</p>"
        )
    return f"""<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><title>{escape(title)}</title>
    <style>@page{{size:letter;margin:20mm}}body{{font-family:Helvetica;color:#17181c}}header{{border-bottom:3px solid #ed111c;padding-bottom:14px}}
    h1{{margin:0}}h2{{color:#ed111c}}dl{{margin-top:30px}}dt{{font-size:9pt;color:#666}}dd{{margin:4px 0 18px;font-weight:bold}}
    table{{width:100%;border-collapse:collapse;font-size:9pt}}th{{background:#17181c;color:white;text-align:left;padding:7px}}td{{border-bottom:1px solid #ddd;padding:7px}}
    .evidence-photo{{width:120px;height:auto;object-fit:contain}}
    .sign{{margin-top:70px;display:flex;justify-content:space-between}}.sign span{{width:42%;border-top:1px solid #333;padding-top:7px;text-align:center}}</style></head>
    <body><header><h1>SMARTDIAG504</h1><h2>{escape(title)}</h2></header><dl><dt>Orden de trabajo</dt><dd>{escape(work_order.number)}</dd>
    <dt>Cliente</dt><dd>{escape(work_order.customer_name)}</dd><dt>Vehiculo</dt><dd>{escape(work_order.vehicle_label)}</dd>
    <dt>Estado</dt><dd>{escape(work_order.status)}</dd><dt>Diagnostico</dt><dd>{escape(work_order.diagnosis or 'Sin observaciones adicionales')}</dd></dl>
    {evidence_section}<p>Documento generado desde la trazabilidad registrada en SmartDiag504.</p><div class=\"sign\"><span>Responsable del taller</span><span>Firma del cliente</span></div></body></html>"""


def warehouse_document_html(work_order: WorkOrder, kind: str) -> str:
    titles = {"picking-ticket": "Ticket de picking", "delivery": "Entrega de repuestos a OT",
              "return": "Devolucion de repuestos", "receipt": "Entrada de mercancia"}
    rows = "".join(
        f"<tr><td>{escape(str(part.get('sku', '')))}</td><td>{escape(str(part.get('name', '')))}</td>"
        f"<td>{escape(str(part.get('quantity', '')))}</td><td>{escape(str(part.get('location', '')))}</td>"
        f"<td>{escape(str(part.get('status', '')))}</td></tr>" for part in (work_order.parts_required or [])
    )
    return f"""<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><title>{escape(titles[kind])}</title>
    <style>@page{{size:letter;margin:18mm}}body{{font-family:Helvetica;color:#17181c}}header{{border-bottom:3px solid #ed111c;padding-bottom:12px}}h1{{margin:0}}h2{{color:#ed111c}}
    table{{width:100%;border-collapse:collapse;margin-top:20px}}th{{background:#17181c;color:#fff;text-align:left;padding:8px}}td{{border-bottom:1px solid #ddd;padding:8px}}.sign{{margin-top:70px}}</style></head>
    <body><header><h1>SMARTDIAG504</h1><h2>{escape(titles[kind])}</h2></header><p><b>OT:</b> {escape(work_order.number)} &nbsp; <b>Vehiculo:</b> {escape(work_order.vehicle_label)}</p>
    <table><thead><tr><th>Codigo</th><th>Repuesto</th><th>Cantidad</th><th>Ubicacion</th><th>Estado</th></tr></thead><tbody>{rows}</tbody></table>
    <p class=\"sign\">Responsable: ____________________ &nbsp;&nbsp; Recibe: ____________________ &nbsp;&nbsp; Fecha: __________</p></body></html>"""
