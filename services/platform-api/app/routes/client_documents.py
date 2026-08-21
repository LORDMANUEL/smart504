from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from app.client_auth import require_client
from app.db import get_db
from app.models import ClientUser, Customer, Payment, Quote, Vehicle, WorkOrder
from app.services.document_templates import persist_render, render_published_or_fallback
from app.services.documents import html_to_pdf, quote_html, quote_template_context
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

router = APIRouter(prefix="/api/v1/client-documents", tags=["client-documents"])


def _client_quote(db: Session, quote_id: str, client_user: ClientUser) -> tuple[Quote, WorkOrder]:
    customer_id = client_user.customer_id
    quote = db.scalar(
        select(Quote)
        .join(WorkOrder, Quote.work_order_id == WorkOrder.id)
        .where(Quote.id == quote_id, WorkOrder.customer_id == customer_id)
        .options(selectinload(Quote.lines))
    )
    if quote is None:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    work_order = db.get(WorkOrder, quote.work_order_id)
    if work_order is None:
        raise HTTPException(status_code=404, detail="OT no encontrada")
    return quote, work_order


@router.get("/quotes/{quote_id}.html", response_class=HTMLResponse)
def client_quote_html(
    quote_id: str,
    client_user: ClientUser = Depends(require_client),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    quote, work_order = _client_quote(db, quote_id, client_user)
    fallback = quote_html(quote, work_order)
    html, _, _ = render_published_or_fallback(db, "QUOTE", quote_template_context(quote, work_order), fallback)
    return HTMLResponse(html)


@router.get("/quotes/{quote_id}.pdf")
def client_quote_pdf(
    quote_id: str,
    client_user: ClientUser = Depends(require_client),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    quote, work_order = _client_quote(db, quote_id, client_user)
    fallback = quote_html(quote, work_order)
    html, template, version = render_published_or_fallback(db, "QUOTE", quote_template_context(quote, work_order), fallback)
    persist_render(db, "QUOTE", quote.number, html, client_user.email, template, version)
    db.commit()
    return StreamingResponse(
        html_to_pdf(html),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{quote.number}.pdf"'},
    )


@router.get("/invoices/{invoice_number}.pdf")
def invoice_pdf(
    invoice_number: str,
    client_user: ClientUser = Depends(require_client),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    work_order = db.scalar(select(WorkOrder).where(
        WorkOrder.customer_id == client_user.customer_id,
        WorkOrder.invoice_reference == invoice_number,
    ))
    if work_order is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    customer = db.get(Customer, client_user.customer_id)
    vehicle = db.get(Vehicle, work_order.vehicle_id)
    payment = db.scalar(select(Payment).where(Payment.work_order_id == work_order.id).order_by(Payment.created_at.desc()))
    total = str(payment.amount if payment else 0)
    context = {
        "company.name": "SmartDiag504", "company.legal_name": "SmartDiag504",
        "company.tax_id": "", "company.address": "Tegucigalpa, Honduras", "company.phone": "",
        "document.number": invoice_number, "document.date": work_order.updated_at.date().isoformat(), "document.title": "Factura",
        "customer.name": customer.full_name if customer else client_user.full_name,
        "customer.phone": customer.phone if customer else "",
        "vehicle.label": f"{vehicle.make} {vehicle.model} {vehicle.model_year or ''}" if vehicle else "",
        "vehicle.vin": vehicle.vin if vehicle else "", "work_order.number": work_order.number,
        "work_order.status": work_order.status, "work_order.diagnosis": work_order.diagnosis or "",
        "quote.subtotal": total, "quote.discount": "0.00", "quote.tax": "0.00", "quote.total": total,
        "quote.rows_html": f"<tr><td>{work_order.number}</td><td>{work_order.title}</td><td>1</td><td>{total}</td></tr>",
        "document.notes": "Documento emitido desde el historial autorizado del cliente.",
    }
    fallback = f"""<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><style>@page{{size:letter;margin:18mm}}body{{font-family:Helvetica}}header{{border-bottom:3px solid #ed111c}}table{{width:100%;margin-top:25px}}td{{padding:8px;border-bottom:1px solid #ddd}}</style></head><body><header><h1>SMARTDIAG504</h1><h2>Factura {invoice_number}</h2></header><p>Cliente: {context['customer.name']}</p><table>{context['quote.rows_html']}</table><h2>Total: {total}</h2></body></html>"""
    html, template, version = render_published_or_fallback(db, "INVOICE", context, fallback)
    persist_render(db, "INVOICE", invoice_number, html, client_user.email, template, version)
    db.commit()
    return StreamingResponse(
        html_to_pdf(html),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{invoice_number}.pdf"'},
    )
