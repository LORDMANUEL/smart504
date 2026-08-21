from __future__ import annotations

import uuid
import hmac
import secrets
from html import escape
from types import SimpleNamespace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import require_admin
from app.request_context import audit_actor, current_identity
from app.db import get_db
from app.config import get_settings
from app.models import (
    Branch,
    ApprovalRequest,
    CashSession,
    CatalogProduct,
    CounterItemRequest,
    Customer,
    FlowEvent,
    InventoryBalance,
    InventoryMovement,
    Payment,
    Quote,
    QuoteLine,
    RetailReturn,
    RetailReturnItem,
    RetailSale,
    RetailSaleItem,
    Vehicle,
    WarehouseLocation,
    WorkOrder,
    WorkOrderLaborEntry,
)
from app.schemas import (
    ApprovalRequestCreate,
    ApprovalRequestRead,
    CashSessionClose,
    CashSessionOpen,
    CashSessionRead,
    CashSummary,
    CounterReturnCreate,
    CounterItemRequestCreate,
    CounterItemRequestRead,
    CounterReturnRead,
    CounterSaleCreate,
    CounterSaleRead,
    PaymentCreate,
    PaymentRead,
    QuoteCreate,
    QuoteConvertCreate,
    QuoteFromWorkOrderCreate,
    QuoteLineStatusUpdate,
    QuoteRead,
    QuoteStatusUpdate,
    WorkOrderCreate,
)
from app.services.document_templates import persist_render, render_published_or_fallback
from app.services.counter_sales_sync import synchronize_retail_return, synchronize_retail_sale
from app.services.approval_email import send_approval_email
from app.services.approvals import token_digest
from app.services.pricing import product_pricing_policy, validate_transaction_floor
from app.services.inventory_analysis import inventory_policy_report
from app.services.erp_outbox import enqueue_erp_job
from app.services.branch_scope import operational_branch_id
from app.services.documents import (
    html_to_pdf,
    quote_html,
    quote_template_context,
    warehouse_document_html,
    warehouse_template_context,
    work_order_document_html,
    work_order_template_context,
)
from app.services.work_orders import create_work_order
from app.services.vehicle_fitment import (
    compatible_products,
    find_vehicle_by_vin,
    primary_image_url,
    vehicle_label,
)

router = APIRouter(
    prefix="/api/v1/operations/finance",
    tags=["finance"],
    dependencies=[Depends(require_admin)],
)


def _queue_quote_sync(db: Session, quote: Quote, reason: str) -> None:
    quote.erp_sync_status = "PENDING"
    quote.erp_sync_error = None
    enqueue_erp_job(
        db,
        aggregate_type="QUOTE",
        aggregate_id=quote.id,
        operation="UPSERT_SERVICE_QUOTATION",
        idempotency_key=f"quote:{quote.id}:{reason}",
        payload={},
    )


def require_cashier_code(value: str | None) -> None:
    configured = get_settings().cashier_access_code
    if configured and not hmac.compare_digest(configured.get_secret_value(), value or ""):
        raise HTTPException(status_code=403, detail="Codigo de cajera incorrecto")


def load_quote(db: Session, quote_id: str) -> Quote:
    quote = db.scalar(select(Quote).options(selectinload(Quote.lines)).where(
        Quote.id == quote_id, Quote.organization_id == current_identity().organization_id
    ))
    if quote is None:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return quote


def load_counter_sale(db: Session, sale_id: str) -> RetailSale:
    sale = db.scalar(
        select(RetailSale)
        .options(selectinload(RetailSale.items), selectinload(RetailSale.returns))
        .where(RetailSale.id == sale_id, RetailSale.organization_id == current_identity().organization_id)
    )
    if sale is None:
        raise HTTPException(status_code=404, detail="Venta de mostrador no encontrada")
    return sale


def load_counter_return(db: Session, return_id: str) -> RetailReturn:
    record = db.scalar(
        select(RetailReturn)
        .options(
            selectinload(RetailReturn.items),
            selectinload(RetailReturn.sale).selectinload(RetailSale.items),
        )
        .where(RetailReturn.id == return_id, RetailReturn.organization_id == current_identity().organization_id)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Devolucion de mostrador no encontrada")
    return record


def counter_product_payload(product: CatalogProduct, warehouse_stock: dict[str, str] | None = None) -> dict[str, object]:
    policy = product_pricing_policy(product)
    available = sum((Decimal(value) for value in (warehouse_stock or {}).values()), Decimal("0"))
    blocking_reasons: list[str] = []
    if not product.sku.strip():
        blocking_reasons.append("SIN_ITEM")
    if product.price <= 0:
        blocking_reasons.append("SIN_PRECIO")
    if available <= 0:
        blocking_reasons.append("SIN_EXISTENCIA")
    return {
        "id": product.id, "sku": product.sku, "name": product.name,
        "price": str(product.price), "purchase_cost": str(product.purchase_cost),
        "landed_cost_factor": str(product.landed_cost_factor),
        "target_markup_percent": str(product.target_markup_percent),
        "minimum_sale_price": str(policy.minimum_sale_price),
        "suggested_sale_price": str(policy.suggested_sale_price),
        "abc_class": product.abc_class, "xyz_class": product.xyz_class,
        "stock_qty": str(product.stock_qty), "stock_status": product.stock_status,
        "compatibility_note": product.compatibility_notes,
        "image_url": primary_image_url(product),
        "sellable": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
        **({"warehouse_stock": warehouse_stock} if warehouse_stock is not None else {}),
    }


def counter_sale_payload(db: Session, sale: RetailSale) -> dict[str, object]:
    payment = db.scalar(
        select(Payment)
        .where(Payment.retail_sale_id == sale.id, Payment.status == "CAPTURED")
        .order_by(Payment.created_at.asc())
    )
    return {
        "id": sale.id,
        "organization_id": sale.organization_id,
        "branch_id": sale.branch_id,
        "warehouse_id": sale.warehouse_id,
        "cash_session_id": sale.cash_session_id,
        "sale_number": sale.sale_number,
        "invoice_number": sale.invoice_number,
        "customer_id": sale.customer_id,
        "customer_name": sale.customer_name,
        "phone": sale.phone,
        "tax_id": sale.tax_id,
        "vehicle_vin": sale.vehicle_vin,
        "status": sale.status,
        "currency": sale.currency,
        "subtotal": sale.subtotal,
        "discount": sale.discount,
        "tax": sale.tax,
        "total": sale.total,
        "payment_method": sale.payment_method,
        "payment_reference": sale.payment_reference,
        "erpnext_invoice_id": sale.erpnext_invoice_id,
        "erpnext_payment_id": sale.erpnext_payment_id,
        "sync_status": sale.sync_status,
        "sync_error": sale.sync_error,
        "sync_attempts": sale.sync_attempts,
        "last_sync_at": sale.last_sync_at,
        "created_by": sale.created_by,
        "completed_at": sale.completed_at,
        "created_at": sale.created_at,
        "updated_at": sale.updated_at,
        "items": sale.items,
        "payment": payment,
    }


def counter_sale_html(sale: RetailSale) -> str:
    rows = "".join(
        f"<tr><td>{escape(item.sku)}</td><td>{escape(item.name)}</td>"
        f"<td>{item.quantity}</td><td>L {item.unit_price:,.2f}</td>"
        f"<td>L {item.line_total:,.2f}</td></tr>"
        for item in sale.items
    )
    return f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><style>
    body{{font-family:Arial,sans-serif;color:#17181c;padding:28px}}h1{{margin:0}}small{{color:#687080}}
    table{{width:100%;border-collapse:collapse;margin:22px 0}}th,td{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}
    .totals{{margin-left:auto;width:280px}}.totals p{{display:flex;justify-content:space-between}}
    </style></head><body><h1>SmartDiag504 · Venta por mostrador</h1>
    <p><b>{escape(sale.invoice_number)}</b><br><small>{escape(sale.sale_number)} · {sale.completed_at.isoformat()}</small></p>
    <p>Cliente: {escape(sale.customer_name)} · RTN: {escape(sale.tax_id or 'Consumidor final')}<br>
    Teléfono: {escape(sale.phone or 'No indicado')} · VIN: {escape(sale.vehicle_vin or 'No aplica')}</p>
    <table><thead><tr><th>SKU</th><th>Producto</th><th>Cant.</th><th>Precio</th><th>Total</th></tr></thead><tbody>{rows}</tbody></table>
    <div class='totals'><p><span>Subtotal</span><b>L {sale.subtotal:,.2f}</b></p>
    <p><span>Descuento</span><b>L {sale.discount:,.2f}</b></p><p><span>Impuesto</span><b>L {sale.tax:,.2f}</b></p>
    <p><span>Total</span><b>L {sale.total:,.2f}</b></p></div>
    <p>Pago: {escape(sale.payment_method)} · Referencia: {escape(sale.payment_reference or 'N/A')}</p>
    <small>Documento operativo. Su validez fiscal depende de la configuración CAI/SAR y sincronización ERP.</small></body></html>"""


@router.get("/counter-sales/context")
def counter_sales_context(warehouse_id: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    organization_id = current_identity().organization_id
    branches = list(db.scalars(select(Branch).where(
        Branch.organization_id == organization_id, Branch.active.is_(True)
    ).order_by(Branch.code)))
    warehouses = list(
        db.scalars(
            select(WarehouseLocation)
            .where(
                WarehouseLocation.active.is_(True),
                WarehouseLocation.organization_id == organization_id,
                WarehouseLocation.warehouse_type == "STOCK",
            )
            .order_by(WarehouseLocation.code)
        )
    )
    products = list(
        db.scalars(
            select(CatalogProduct)
            .where(CatalogProduct.organization_id == organization_id, CatalogProduct.active.is_(True))
            .options(selectinload(CatalogProduct.images))
            .order_by(CatalogProduct.name)
            .limit(500)
        )
    )
    balance_query = select(InventoryBalance).where(InventoryBalance.organization_id == organization_id)
    if warehouse_id:
        balance_query = balance_query.where(InventoryBalance.warehouse_id == warehouse_id)
    balances = list(db.scalars(balance_query))
    availability: dict[str, dict[str, str]] = {}
    for balance in balances:
        availability.setdefault(balance.product_id, {})[balance.warehouse_id] = str(
            balance.quantity_on_hand - balance.quantity_reserved
        )
    return {
        "owner_approval_email": get_settings().owner_approval_email,
        "branches": [{"id": item.id, "code": item.code, "name": item.name} for item in branches],
        "warehouses": [
            {"id": item.id, "branch_id": item.branch_id, "code": item.code, "name": item.name}
            for item in warehouses
        ],
        "products": [counter_product_payload(item, availability.get(item.id, {})) for item in products],
    }


@router.get("/counter-item-requests", response_model=list[CounterItemRequestRead])
def list_counter_item_requests(db: Session = Depends(get_db)) -> list[CounterItemRequest]:
    return list(db.scalars(select(CounterItemRequest).where(
        CounterItemRequest.organization_id == current_identity().organization_id
    ).order_by(CounterItemRequest.created_at.desc()).limit(300)))


@router.post("/counter-item-requests", response_model=CounterItemRequestRead, status_code=201)
def create_counter_item_request(data: CounterItemRequestCreate, db: Session = Depends(get_db)) -> CounterItemRequest:
    organization_id = current_identity().organization_id
    branch = db.scalar(select(Branch).where(Branch.id == data.branch_id, Branch.organization_id == organization_id))
    if branch is None or not branch.active:
        raise HTTPException(status_code=422, detail="Sucursal no válida")
    if data.warehouse_id:
        warehouse = db.scalar(select(WarehouseLocation).where(WarehouseLocation.id == data.warehouse_id, WarehouseLocation.organization_id == organization_id))
        if warehouse is None or warehouse.branch_id != branch.id:
            raise HTTPException(status_code=422, detail="Bodega no válida para la sucursal")
    if data.product_id and db.scalar(select(CatalogProduct.id).where(CatalogProduct.id == data.product_id, CatalogProduct.organization_id == organization_id)) is None:
        raise HTTPException(status_code=422, detail="El artículo seleccionado no existe")
    stamp = datetime.now(UTC)
    record = CounterItemRequest(
        organization_id=branch.organization_id,
        number=f"SOL-MOST-{stamp:%y%m%d}-{uuid.uuid4().hex[:6].upper()}",
        branch_id=branch.id,
        warehouse_id=data.warehouse_id,
        product_id=data.product_id,
        search_query=data.search_query.strip(),
        customer_name=data.customer_name.strip(),
        phone=data.phone,
        vehicle_vin=data.vehicle_vin.upper() if data.vehicle_vin else None,
        quantity=data.quantity,
        notes=data.notes,
        requested_by=audit_actor(None),
    )
    db.add(record)
    db.add(FlowEvent(module="COUNTER_SALES", action="ITEM_REQUESTED", item_reference=record.number, actor=record.requested_by, result="SUCCESS", metadata_json={"query": record.search_query, "vin": record.vehicle_vin, "quantity": str(record.quantity)}))
    db.commit()
    db.refresh(record)
    return record


@router.get("/counter-sales/fitment")
def counter_sales_fitment(vin: str, db: Session = Depends(get_db)) -> dict[str, object]:
    vehicle = find_vehicle_by_vin(db, vin)
    if vehicle is None:
        return {"status": "NOT_FOUND", "vehicle": None, "products": []}
    products = compatible_products(db, vehicle)
    return {
        "status": "MATCHED",
        "vehicle": {
            "id": vehicle.id,
            "customer_id": vehicle.customer_id,
            "label": vehicle_label(vehicle),
            "make": vehicle.make,
            "model": vehicle.model,
            "model_year": vehicle.model_year,
            "vin": vehicle.vin,
            "plate": vehicle.plate,
            "owner": vehicle.customer.full_name if vehicle.customer else None,
        },
        "products": [counter_product_payload(item) for item in products],
    }


@router.get("/counter-sales", response_model=list[CounterSaleRead])
def list_counter_sales(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    sales = list(
        db.scalars(
            select(RetailSale)
            .where(RetailSale.organization_id == current_identity().organization_id)
            .options(selectinload(RetailSale.items))
            .order_by(RetailSale.created_at.desc())
            .limit(200)
        ).unique()
    )
    return [counter_sale_payload(db, sale) for sale in sales]


@router.post("/counter-sales", response_model=CounterSaleRead, status_code=201)
def create_counter_sale(data: CounterSaleCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    require_cashier_code(data.access_code)
    organization_id = current_identity().organization_id
    session = db.scalar(select(CashSession).where(CashSession.id == data.cash_session_id, CashSession.organization_id == organization_id))
    if session is None or session.status != "OPEN":
        raise HTTPException(status_code=409, detail="Debe abrir un turno de caja para vender")
    branch = db.scalar(select(Branch).where(Branch.id == data.branch_id, Branch.organization_id == organization_id))
    warehouse = db.scalar(select(WarehouseLocation).where(WarehouseLocation.id == data.warehouse_id, WarehouseLocation.organization_id == organization_id))
    if branch is None or warehouse is None or warehouse.branch_id != branch.id or not warehouse.active:
        raise HTTPException(status_code=422, detail="Sucursal o bodega de mostrador no válida")
    if data.method in {"CARD", "TRANSFER"} and not data.reference:
        raise HTTPException(status_code=422, detail="Tarjeta y transferencia requieren referencia")
    if data.customer_id and db.scalar(select(Customer.id).where(Customer.id == data.customer_id, Customer.organization_id == organization_id)) is None:
        raise HTTPException(status_code=422, detail="El cliente indicado no existe")

    lines: list[RetailSaleItem] = []
    movements: list[tuple[CatalogProduct, Decimal]] = []
    subtotal = Decimal("0.00")
    pricing_lines: list[tuple[Decimal, Decimal, Decimal]] = []
    seen: set[str] = set()
    for requested in data.items:
        if requested.product_id in seen:
            raise HTTPException(status_code=422, detail="No repita el mismo producto en la venta")
        seen.add(requested.product_id)
        product = db.scalar(select(CatalogProduct).where(CatalogProduct.id == requested.product_id, CatalogProduct.organization_id == organization_id))
        if product is None or not product.active:
            raise HTTPException(status_code=422, detail="Producto no disponible")
        if not product.sku.strip():
            raise HTTPException(status_code=422, detail="No se puede vender un artículo sin código")
        if product.price <= 0:
            raise HTTPException(status_code=422, detail=f"{product.sku} no tiene precio de venta")
        if requested.unit_price != product.price:
            raise HTTPException(status_code=422, detail=f"El precio de {product.sku} debe venir del catálogo")
        balance = db.scalar(
            select(InventoryBalance)
            .where(
                InventoryBalance.warehouse_id == warehouse.id,
                InventoryBalance.product_id == product.id,
            )
            .with_for_update()
        )
        if balance is None:
            raise HTTPException(status_code=409, detail=f"{product.sku} no tiene existencia registrada en esta bodega")
        available = balance.quantity_on_hand - balance.quantity_reserved
        if available < requested.quantity:
            raise HTTPException(status_code=409, detail=f"Existencia insuficiente para {product.sku}")
        line_total = requested.quantity * requested.unit_price
        policy = product_pricing_policy(product)
        pricing_lines.append((requested.quantity, requested.unit_price, policy.minimum_sale_price))
        subtotal += line_total
        lines.append(
            RetailSaleItem(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                quantity=requested.quantity,
                unit_price=requested.unit_price,
                unit_cost=policy.landed_cost,
                line_total=line_total,
            )
        )
        balance.quantity_on_hand -= requested.quantity
        product.stock_qty -= requested.quantity
        product.stock_status = "OUT_OF_STOCK" if product.stock_qty <= 0 else "IN_STOCK"
        movements.append((product, requested.quantity))
    validate_transaction_floor(lines=pricing_lines, discount=data.discount)
    total = subtotal - data.discount + data.tax
    if total <= 0:
        raise HTTPException(status_code=422, detail="El total de la venta debe ser mayor que cero")

    stamp = datetime.now(UTC)
    suffix = uuid.uuid4().hex[:6].upper()
    sale = RetailSale(
        organization_id=branch.organization_id,
        branch_id=branch.id,
        warehouse_id=warehouse.id,
        cash_session_id=session.id,
        sale_number=f"MOST-{stamp:%y%m%d}-{suffix}",
        invoice_number=f"FAC-M-{stamp:%y%m%d}-{suffix}",
        customer_id=data.customer_id,
        customer_name=data.customer_name,
        phone=data.phone,
        tax_id=data.tax_id,
        vehicle_vin=data.vehicle_vin,
        subtotal=subtotal,
        discount=data.discount,
        tax=data.tax,
        total=total,
        payment_method=data.method,
        payment_reference=data.reference,
        created_by=audit_actor(data.actor),
        items=lines,
    )
    db.add(sale)
    db.flush()
    for product, quantity in movements:
        db.add(
            InventoryMovement(
                organization_id=branch.organization_id,
                warehouse_id=warehouse.id,
                product_id=product.id,
                movement_type="COUNTER_SALE",
                quantity=-quantity,
                reference=sale.sale_number,
                actor=audit_actor(data.actor),
            )
        )
    payment = Payment(
        organization_id=sale.organization_id,
        branch_id=sale.branch_id,
        receipt_number=f"REC-M-{stamp:%y%m%d}-{suffix}",
        cash_session_id=session.id,
        work_order_id=None,
        quote_id=None,
        retail_sale_id=sale.id,
        method=data.method,
        amount=total,
        reference=data.reference,
        received_by=audit_actor(data.actor),
    )
    db.add(payment)
    db.add(
        FlowEvent(
            module="COUNTER_SALES",
            action="COUNTER_SALE_COMPLETED",
            item_reference=sale.sale_number,
            actor=audit_actor(data.actor),
            result="SUCCESS",
            metadata_json={"invoice": sale.invoice_number, "total": str(total), "items": len(lines)},
        )
    )
    db.commit()
    synchronize_retail_sale(db, sale, warehouse, get_settings())
    return counter_sale_payload(db, load_counter_sale(db, sale.id))


@router.post("/counter-sales/{sale_id}/sync", response_model=CounterSaleRead)
def retry_counter_sale_sync(sale_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    sale = load_counter_sale(db, sale_id)
    warehouse = db.get(WarehouseLocation, sale.warehouse_id)
    if warehouse is None:
        raise HTTPException(status_code=409, detail="La bodega de la venta ya no existe")
    synchronize_retail_sale(db, sale, warehouse, get_settings())
    return counter_sale_payload(db, load_counter_sale(db, sale.id))


@router.get("/counter-sales/{sale_id}.pdf")
def printable_counter_sale(sale_id: str, db: Session = Depends(get_db)) -> StreamingResponse:
    sale = load_counter_sale(db, sale_id)
    html = counter_sale_html(sale)
    persist_render(db, "INVOICE", sale.invoice_number, html, sale.created_by, None, None)
    db.commit()
    return StreamingResponse(
        html_to_pdf(html),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{sale.invoice_number}.pdf"'},
    )


@router.post(
    "/counter-sales/{sale_id}/approval-requests",
    response_model=ApprovalRequestRead,
    status_code=201,
)
def create_counter_approval_request(
    sale_id: str, data: ApprovalRequestCreate, db: Session = Depends(get_db)
) -> dict[str, object]:
    sale = load_counter_sale(db, sale_id)
    items_by_id = {item.id: item for item in sale.items}
    normalized_items: list[dict[str, str]] = []
    for requested in data.items:
        item = items_by_id.get(requested.sale_item_id)
        if item is None:
            raise HTTPException(status_code=422, detail="El articulo no pertenece a esta venta")
        available = item.quantity - item.returned_quantity
        if requested.quantity > available:
            raise HTTPException(status_code=409, detail=f"La solicitud excede lo vendido de {item.sku}")
        normalized_items.append({"sale_item_id": item.id, "sku": item.sku, "quantity": str(requested.quantity)})
    token = secrets.token_urlsafe(32)
    settings = get_settings()
    approval_url = f"{settings.approval_public_base_url.rstrip('/')}/api/v1/public/approvals/{token}"
    approval = ApprovalRequest(
        sale_id=sale.id,
        request_type=data.request_type,
        requested_by=audit_actor(data.requested_by),
        owner_email=str(data.owner_email),
        reason=data.reason,
        payload_json={
            "sale_number": sale.sale_number, "invoice_number": sale.invoice_number,
            "method": data.method, "reference": data.reference, "items": normalized_items,
        },
        token_hash=token_digest(token),
        expires_at=datetime.now(UTC) + timedelta(hours=settings.approval_expiry_hours),
    )
    delivery_status, delivery_error = send_approval_email(
        settings=settings, recipient=approval.owner_email, request_type=approval.request_type,
        reference=sale.invoice_number, reason=approval.reason, approval_url=approval_url,
    )
    approval.delivery_status = delivery_status
    approval.delivery_error = delivery_error
    db.add(approval)
    db.add(FlowEvent(module="APPROVALS", action=f"{data.request_type}_REQUESTED", item_reference=sale.sale_number, actor=audit_actor(data.requested_by), result="SUCCESS", metadata_json={"owner_email": approval.owner_email, "delivery_status": delivery_status}))
    db.commit()
    db.refresh(approval)
    payload = ApprovalRequestRead.model_validate(approval).model_dump()
    payload.update({"token": token, "approval_url": approval_url})
    return payload


@router.get("/approval-requests", response_model=list[ApprovalRequestRead])
def list_approval_requests(db: Session = Depends(get_db)) -> list[ApprovalRequest]:
    return list(db.scalars(select(ApprovalRequest).where(
        ApprovalRequest.organization_id == current_identity().organization_id
    ).order_by(ApprovalRequest.created_at.desc()).limit(200)))


@router.get("/reporting/summary")
def management_reporting_summary(db: Session = Depends(get_db)) -> dict[str, object]:
    organization_id = current_identity().organization_id
    sales = list(db.scalars(select(RetailSale).where(RetailSale.organization_id == organization_id).options(selectinload(RetailSale.items))))
    approvals = list(db.scalars(select(ApprovalRequest).where(ApprovalRequest.organization_id == organization_id)))
    quotes = list(db.scalars(select(Quote).where(Quote.organization_id == organization_id)))
    gross_sales = sum((sale.total for sale in sales), Decimal("0"))
    refunds = sum((record.total for record in db.scalars(select(RetailReturn).where(RetailReturn.organization_id == organization_id))), Decimal("0"))
    net_cost = sum(
        (
            (item.quantity - item.returned_quantity) * item.unit_cost
            for sale in sales for item in sale.items
        ),
        Decimal("0"),
    )
    net_sales = gross_sales - refunds
    gross_profit = net_sales - net_cost
    return {
        "currency": "HNL",
        "gross_sales": str(gross_sales), "refunds": str(refunds),
        "net_sales": str(net_sales), "net_cost": str(net_cost),
        "gross_profit": str(gross_profit),
        "gross_margin_percent": str((gross_profit / net_sales * 100).quantize(Decimal('0.01')) if net_sales else Decimal('0')),
        "erp_pending": sum(1 for sale in sales if sale.sync_status != "SYNCED"),
        "quotes_by_status": {status: sum(1 for quote in quotes if quote.status == status) for status in ("DRAFT", "SENT", "APPROVED", "REJECTED")},
        "approvals_by_status": {status: sum(1 for item in approvals if item.status == status) for status in ("PENDING", "APPROVED", "REJECTED", "CONSUMED", "EXPIRED")},
        "inventory_policy": inventory_policy_report(db),
        "accounting_source": "ERPNext",
        "operational_projection": "SmartDiag504 PostgreSQL",
    }


@router.post("/counter-sales/{sale_id}/returns", response_model=CounterReturnRead, status_code=201)
def return_counter_sale(
    sale_id: str, data: CounterReturnCreate, db: Session = Depends(get_db)
) -> RetailReturn:
    require_cashier_code(data.access_code)
    sale = load_counter_sale(db, sale_id)
    approval = db.scalar(
        select(ApprovalRequest)
        .where(
            ApprovalRequest.id == data.approval_id,
            ApprovalRequest.organization_id == current_identity().organization_id,
        )
        .with_for_update()
    )
    if approval is None or approval.sale_id != sale.id or approval.request_type != "RETURN":
        raise HTTPException(status_code=422, detail="La autorizacion no corresponde a esta devolucion")
    if approval.status != "APPROVED":
        raise HTTPException(status_code=409, detail="La devolucion requiere autorizacion aprobada por el propietario")
    approved_items = {
        (str(item.get("sale_item_id")), Decimal(str(item.get("quantity"))))
        for item in approval.payload_json.get("items", [])
    }
    requested_items = {(item.sale_item_id, item.quantity) for item in data.items}
    if approved_items != requested_items or approval.reason != data.reason or approval.payload_json.get("method") != data.method:
        raise HTTPException(status_code=409, detail="La devolucion cambio despues de ser autorizada; solicite una nueva aprobacion")
    session = db.scalar(select(CashSession).where(
        CashSession.id == sale.cash_session_id,
        CashSession.organization_id == current_identity().organization_id,
    ))
    if session is None or session.status != "OPEN":
        raise HTTPException(status_code=409, detail="La devolución requiere un turno de caja abierto")
    if data.method in {"CARD", "TRANSFER"} and not data.reference:
        raise HTTPException(status_code=422, detail="La devolución requiere referencia del medio")
    items_by_id = {item.id: item for item in sale.items}
    ratio = sale.total / sale.subtotal if sale.subtotal else Decimal("0")
    return_lines: list[RetailReturnItem] = []
    refund = Decimal("0.00")
    for requested in data.items:
        item = items_by_id.get(requested.sale_item_id)
        if item is None:
            raise HTTPException(status_code=422, detail="El artículo no pertenece a esta venta")
        available = item.quantity - item.returned_quantity
        if requested.quantity > available:
            raise HTTPException(status_code=409, detail=f"La devolución excede lo vendido de {item.sku}")
        unit_refund = (item.unit_price * ratio).quantize(Decimal("0.01"))
        line_total = (requested.quantity * unit_refund).quantize(Decimal("0.01"))
        refund += line_total
        item.returned_quantity += requested.quantity
        product = db.scalar(select(CatalogProduct).where(
            CatalogProduct.id == item.product_id,
            CatalogProduct.organization_id == current_identity().organization_id,
        ))
        if product:
            product.stock_qty += requested.quantity
            product.stock_status = "IN_STOCK"
        balance = db.scalar(
            select(InventoryBalance)
            .where(
                InventoryBalance.warehouse_id == sale.warehouse_id,
                InventoryBalance.product_id == item.product_id,
            )
            .with_for_update()
        )
        if balance:
            balance.quantity_on_hand += requested.quantity
        return_lines.append(
            RetailReturnItem(
                sale_item_id=item.id,
                quantity=requested.quantity,
                unit_refund=unit_refund,
                line_total=line_total,
            )
        )
    stamp = datetime.now(UTC)
    suffix = uuid.uuid4().hex[:6].upper()
    record = RetailReturn(
        sale_id=sale.id,
        return_number=f"DEV-M-{stamp:%y%m%d}-{suffix}",
        reason=data.reason,
        method=data.method,
        reference=data.reference,
        subtotal=refund,
        total=refund,
        actor=audit_actor(data.actor),
        items=return_lines,
    )
    fully_returned = all(item.returned_quantity >= item.quantity for item in sale.items)
    sale.status = "RETURNED" if fully_returned else "PARTIAL_RETURN"
    approval.status = "CONSUMED"
    approval.consumed_at = datetime.now(UTC)
    db.add(record)
    db.flush()
    for line in return_lines:
        sale_item = items_by_id[line.sale_item_id]
        db.add(
            InventoryMovement(
                organization_id=sale.organization_id,
                warehouse_id=sale.warehouse_id,
                product_id=sale_item.product_id,
                movement_type="COUNTER_RETURN",
                quantity=line.quantity,
                reference=record.return_number,
                actor=audit_actor(data.actor),
            )
        )
    db.add(
        Payment(
            organization_id=sale.organization_id,
            branch_id=sale.branch_id,
            receipt_number=f"DEV-REC-{stamp:%y%m%d}-{suffix}",
            cash_session_id=session.id,
            work_order_id=None,
            quote_id=None,
            retail_sale_id=sale.id,
            method=data.method,
            amount=-refund,
            reference=data.reference,
            status="CAPTURED",
            received_by=audit_actor(data.actor),
        )
    )
    db.add(
        FlowEvent(
            module="COUNTER_SALES",
            action="COUNTER_SALE_RETURNED",
            item_reference=record.return_number,
            actor=audit_actor(data.actor),
            result="SUCCESS",
            metadata_json={"sale": sale.sale_number, "refund": str(refund)},
        )
    )
    db.commit()
    record = load_counter_return(db, record.id)
    warehouse = db.get(WarehouseLocation, sale.warehouse_id)
    if warehouse:
        synchronize_retail_return(db, sale, record, warehouse, get_settings())
    return load_counter_return(db, record.id)


@router.post("/counter-returns/{return_id}/sync", response_model=CounterReturnRead)
def retry_counter_return_sync(return_id: str, db: Session = Depends(get_db)) -> RetailReturn:
    record = load_counter_return(db, return_id)
    warehouse = db.get(WarehouseLocation, record.sale.warehouse_id)
    if warehouse is None:
        raise HTTPException(status_code=409, detail="La bodega de la devolucion ya no existe")
    synchronize_retail_return(db, record.sale, record, warehouse, get_settings())
    return load_counter_return(db, record.id)


def quote_context(db: Session, quote: Quote) -> WorkOrder | SimpleNamespace:
    organization_id = current_identity().organization_id
    if quote.work_order_id:
        work_order = db.scalar(select(WorkOrder).where(
            WorkOrder.id == quote.work_order_id, WorkOrder.organization_id == organization_id
        ))
        if work_order:
            return work_order
    vehicle = db.scalar(select(Vehicle).where(Vehicle.id == quote.vehicle_id, Vehicle.organization_id == organization_id)) if quote.vehicle_id else None
    customer = db.scalar(select(Customer).where(Customer.id == quote.customer_id, Customer.organization_id == organization_id)) if quote.customer_id else None
    if not vehicle or not customer:
        raise HTTPException(status_code=409, detail="La cotizacion no tiene cliente y vehiculo validos")
    year = f" {vehicle.model_year}" if vehicle.model_year else ""
    plate = f" · {vehicle.plate}" if vehicle.plate else ""
    return SimpleNamespace(number="PRE-OT", customer_name=customer.full_name,
                           vehicle_label=f"{vehicle.make} {vehicle.model}{year}{plate}")


@router.get("/quote-context")
def search_quote_context(query: str, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    term = f"%{query.strip()}%"
    vehicles = list(db.scalars(select(Vehicle).join(Customer).where(or_(
        Vehicle.vin.ilike(term), Vehicle.plate.ilike(term), Customer.full_name.ilike(term),
        Customer.phone.ilike(term), Customer.email.ilike(term),
    )).where(Vehicle.organization_id == current_identity().organization_id,
             Customer.organization_id == current_identity().organization_id)
      .order_by(Customer.full_name, Vehicle.make).limit(20)))
    return [{"vehicle_id": vehicle.id, "customer_id": vehicle.customer_id,
             "vin": vehicle.vin, "plate": vehicle.plate,
             "vehicle": f"{vehicle.make} {vehicle.model} {vehicle.model_year or ''}".strip(),
             "owner": vehicle.customer.full_name if vehicle.customer else vehicle.customer_id}
            for vehicle in vehicles]


@router.get("/quotes/{quote_id}.html", response_class=HTMLResponse)
def printable_quote_html(quote_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    quote = load_quote(db, quote_id)
    context_object = quote_context(db, quote)
    fallback = quote_html(quote, context_object)
    html, _, _ = render_published_or_fallback(
        db, "QUOTE", quote_template_context(quote, context_object), fallback
    )
    return HTMLResponse(html)


@router.get("/quotes/{quote_id}.pdf")
def printable_quote_pdf(quote_id: str, db: Session = Depends(get_db)) -> StreamingResponse:
    quote = load_quote(db, quote_id)
    context_object = quote_context(db, quote)
    fallback = quote_html(quote, context_object)
    html, template, version = render_published_or_fallback(
        db, "QUOTE", quote_template_context(quote, context_object), fallback
    )
    persist_render(db, "QUOTE", quote.number, html, "admin-print", template, version)
    db.commit()
    return StreamingResponse(
        html_to_pdf(html),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{quote.number}.pdf"'},
    )


@router.get("/work-orders/{work_order_id}/documents/{kind}.pdf")
def work_order_document(work_order_id: str, kind: str, db: Session = Depends(get_db)) -> StreamingResponse:
    if kind not in {"invoice", "warranty", "exit-pass", "diagnosis"}:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    work_order = db.scalar(select(WorkOrder).where(WorkOrder.id == work_order_id, WorkOrder.organization_id == current_identity().organization_id))
    if work_order is None:
        raise HTTPException(status_code=404, detail="OT no encontrada")
    document_types = {"invoice": "INVOICE", "warranty": "WARRANTY", "exit-pass": "EXIT_PASS", "diagnosis": "DIAGNOSIS"}
    titles = {"invoice": "Factura / comprobante de cobro", "warranty": "Certificado de garantia", "exit-pass": "Pase de salida del vehiculo", "diagnosis": "Informe de diagnostico con evidencia"}
    fallback = work_order_document_html(work_order, kind)
    document_type = document_types[kind]
    html, template, version = render_published_or_fallback(
        db, document_type, work_order_template_context(work_order, titles[kind]), fallback
    )
    persist_render(db, document_type, work_order.number, html, "admin-print", template, version)
    db.commit()
    return StreamingResponse(
        html_to_pdf(html), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{work_order.number}-{kind}.pdf"'},
    )


@router.get("/work-orders/{work_order_id}/warehouse-documents/{kind}.pdf")
def warehouse_document(work_order_id: str, kind: str, db: Session = Depends(get_db)) -> StreamingResponse:
    if kind not in {"picking-ticket", "delivery", "return", "receipt"}:
        raise HTTPException(status_code=404, detail="Tipo de documento de bodega no encontrado")
    work_order = db.scalar(select(WorkOrder).where(WorkOrder.id == work_order_id, WorkOrder.organization_id == current_identity().organization_id))
    if work_order is None:
        raise HTTPException(status_code=404, detail="OT no encontrada")
    document_types = {"picking-ticket": "PICKING_TICKET", "delivery": "WAREHOUSE_DELIVERY", "return": "WAREHOUSE_RETURN", "receipt": "WAREHOUSE_RECEIPT"}
    titles = {"picking-ticket": "Ticket de picking", "delivery": "Entrega de repuestos a OT", "return": "Devolucion de repuestos", "receipt": "Entrada de mercancia"}
    fallback = warehouse_document_html(work_order, kind)
    document_type = document_types[kind]
    html, template, version = render_published_or_fallback(
        db, document_type, warehouse_template_context(work_order, titles[kind]), fallback
    )
    persist_render(db, document_type, work_order.number, html, "admin-print", template, version)
    db.commit()
    return StreamingResponse(html_to_pdf(html), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{work_order.number}-{kind}.pdf"'})


@router.get("/quotes", response_model=list[QuoteRead])
def list_quotes(db: Session = Depends(get_db)) -> list[Quote]:
    return list(
        db.scalars(
            select(Quote).options(selectinload(Quote.lines)).order_by(Quote.created_at.desc())
            .where(Quote.organization_id == current_identity().organization_id)
        ).unique()
    )


@router.post("/quotes", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
def create_quote(data: QuoteCreate, db: Session = Depends(get_db)) -> Quote:
    organization_id = current_identity().organization_id
    work_order = db.scalar(select(WorkOrder).where(WorkOrder.id == data.work_order_id, WorkOrder.organization_id == organization_id)) if data.work_order_id else None
    if data.work_order_id and work_order is None:
        raise HTTPException(status_code=422, detail="La OT no existe")
    customer_id = work_order.customer_id if work_order else data.customer_id
    vehicle_id = work_order.vehicle_id if work_order else data.vehicle_id
    vehicle = db.scalar(select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.organization_id == organization_id)) if vehicle_id else None
    if not customer_id or not vehicle or vehicle.customer_id != customer_id:
        raise HTTPException(status_code=422, detail="El vehiculo no pertenece al cliente indicado")
    quote_lines: list[QuoteLine] = []
    pricing_lines: list[tuple[Decimal, Decimal, Decimal]] = []
    for requested in data.lines:
        values = requested.model_dump()
        minimum_price = requested.unit_cost
        if requested.line_type == "PART":
            product = db.scalar(
                select(CatalogProduct).where(
                    CatalogProduct.organization_id == organization_id,
                    or_(CatalogProduct.id == requested.source_reference, CatalogProduct.sku == requested.code)
                )
            )
            if product:
                policy = product_pricing_policy(product)
                values["unit_cost"] = policy.landed_cost
                values["source_reference"] = product.id
                minimum_price = policy.minimum_sale_price
        quote_lines.append(QuoteLine(**values))
        pricing_lines.append((requested.quantity, requested.unit_price, minimum_price))
    validate_transaction_floor(lines=pricing_lines, discount=data.discount)
    quote = Quote(
        organization_id=organization_id,
        branch_id=work_order.branch_id if work_order else operational_branch_id(db),
        number=f"COT-{datetime.now(UTC):%y%m%d}-{uuid.uuid4().hex[:5].upper()}",
        work_order_id=work_order.id if work_order else None,
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        notes=data.notes,
        discount=data.discount,
        tax=data.tax,
        created_by=audit_actor(data.created_by),
    )
    quote.lines = quote_lines
    db.add(quote)
    db.flush()
    _queue_quote_sync(db, quote, "created")
    if work_order:
        work_order.technician_quote = {
            "quote_id": quote.id, "quote_number": quote.number, "status": quote.status,
            "subtotal": str(quote.subtotal), "grand_total": str(quote.total),
        }
    db.add(
        FlowEvent(
            module="QUOTES",
            action="QUOTE_CREATED",
            item_reference=quote.number,
            actor=audit_actor(data.created_by),
            result="SUCCESS",
            metadata_json={"work_order": work_order.number if work_order else None,
                           "vehicle_id": vehicle_id, "total": str(quote.total)},
        )
    )
    db.commit()
    return load_quote(db, quote.id)


@router.post("/quotes/{quote_id}/convert-to-work-order", response_model=QuoteRead)
def convert_quote_to_work_order(quote_id: str, data: QuoteConvertCreate, db: Session = Depends(get_db)) -> Quote:
    quote = load_quote(db, quote_id)
    if quote.work_order_id or quote.converted_work_order_id:
        raise HTTPException(status_code=409, detail="La cotizacion ya esta vinculada a una OT")
    if quote.status != "APPROVED":
        raise HTTPException(status_code=409, detail="La cotizacion debe estar aprobada")
    if not quote.customer_id or not quote.vehicle_id:
        raise HTTPException(status_code=409, detail="Falta cliente o vehiculo")
    work_order = create_work_order(db, WorkOrderCreate(
        customer_id=quote.customer_id, vehicle_id=quote.vehicle_id, title=data.title,
        concern=data.concern, actor=audit_actor(data.actor),
    ))
    quote.work_order_id = work_order.id
    quote.converted_work_order_id = work_order.id
    work_order.technician_quote = {"quote_id": quote.id, "quote_number": quote.number,
                                   "status": quote.status, "subtotal": str(quote.subtotal),
                                   "grand_total": str(quote.total)}
    db.add(FlowEvent(module="QUOTES", action="QUOTE_CONVERTED_TO_OT", item_reference=quote.number,
                     actor=audit_actor(data.actor), result="SUCCESS", metadata_json={"work_order": work_order.number}))
    db.commit()
    return load_quote(db, quote.id)


@router.post(
    "/quotes/from-work-order/{work_order_id}",
    response_model=QuoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_quote_from_work_order(
    work_order_id: str,
    data: QuoteFromWorkOrderCreate,
    db: Session = Depends(get_db),
) -> Quote:
    work_order = db.scalar(select(WorkOrder).where(
        WorkOrder.id == work_order_id,
        WorkOrder.organization_id == current_identity().organization_id,
    ))
    if work_order is None:
        raise HTTPException(status_code=404, detail="La OT no existe")
    technical = work_order.technician_quote or {}
    lines: list[QuoteLine] = []
    labor_entries = list(
        db.scalars(
            select(WorkOrderLaborEntry)
            .where(WorkOrderLaborEntry.work_order_id == work_order.id)
            .order_by(WorkOrderLaborEntry.created_at)
        )
    )
    for entry in labor_entries:
        lines.append(
            QuoteLine(
                line_type="LABOR",
                code=entry.service_code,
                description=entry.description,
                quantity=entry.hours,
                unit_price=entry.hourly_sale_rate,
                unit_cost=entry.hourly_cost_snapshot,
                approval_status="PENDING",
                source_reference=entry.id,
            )
        )
    labor_total = Decimal(str(technical.get("labor_total", technical.get("labor", "0"))))
    if not labor_entries and labor_total > 0:
        lines.append(
            QuoteLine(
                line_type="LABOR",
                code=str(technical.get("labor_code", "OT-MANO-OBRA")),
                description=str(
                    technical.get("labor_description", "Mano de obra indicada por el técnico")
                ),
                quantity=Decimal("1"),
                unit_price=labor_total,
                unit_cost=Decimal(str(technical.get("labor_cost", "0"))),
                approval_status="PENDING",
                source_reference=work_order.number,
            )
        )
    for index, part in enumerate(work_order.parts_required or [], start=1):
        quantity = Decimal(str(part.get("quantity", "1")))
        unit_price = Decimal(str(part.get("unit_price", part.get("price", "0"))))
        lines.append(
            QuoteLine(
                line_type="PART",
                code=str(part.get("sku", f"OT-PARTE-{index}")),
                description=str(part.get("name", part.get("description", "Repuesto solicitado"))),
                quantity=quantity,
                unit_price=unit_price,
                unit_cost=Decimal(str(part.get("unit_cost", "0"))),
                approval_status="PENDING",
                source_reference=str(part.get("request_id", work_order.number)),
            )
        )
    if not lines:
        raise HTTPException(
            status_code=409,
            detail="La OT todavía no contiene mano de obra ni repuestos para cotizar",
        )
    quote = Quote(
        organization_id=current_identity().organization_id,
        branch_id=work_order.branch_id,
        number=f"COT-{datetime.now(UTC):%y%m%d}-{uuid.uuid4().hex[:5].upper()}",
        work_order_id=work_order.id,
        customer_id=work_order.customer_id,
        vehicle_id=work_order.vehicle_id,
        notes="Cotización armada desde los conceptos registrados en la OT.",
        created_by=audit_actor(data.actor),
        lines=lines,
    )
    db.add(quote)
    db.flush()
    _queue_quote_sync(db, quote, "created-from-work-order")
    work_order.technician_quote = {
        **technical,
        "quote_id": quote.id,
        "quote_number": quote.number,
        "status": quote.status,
        "subtotal": str(quote.subtotal),
        "grand_total": str(quote.total),
    }
    db.add(
        FlowEvent(
            module="QUOTES",
            action="QUOTE_ASSEMBLED_FROM_OT",
            item_reference=quote.number,
            actor=audit_actor(data.actor),
            result="SUCCESS",
            metadata_json={"work_order": work_order.number, "line_count": len(lines)},
        )
    )
    db.commit()
    return load_quote(db, quote.id)


@router.patch("/quotes/{quote_id}/lines/{line_id}", response_model=QuoteRead)
def update_quote_line_status(
    quote_id: str,
    line_id: str,
    data: QuoteLineStatusUpdate,
    db: Session = Depends(get_db),
) -> Quote:
    quote = load_quote(db, quote_id)
    line = next((item for item in quote.lines if item.id == line_id), None)
    if line is None:
        raise HTTPException(status_code=404, detail="Línea de cotización no encontrada")
    if quote.status == "APPROVED":
        raise HTTPException(status_code=409, detail="La cotización aprobada ya no admite cambios")
    previous = line.approval_status
    line.approval_status = data.approval_status
    _queue_quote_sync(db, quote, f"line:{line.id}:{data.approval_status}")
    db.add(
        FlowEvent(
            module="QUOTES",
            action=f"QUOTE_LINE_{data.approval_status}",
            item_reference=quote.number,
            actor=audit_actor(data.actor),
            result="SUCCESS",
            metadata_json={"line_id": line.id, "from": previous, "code": line.code},
        )
    )
    db.commit()
    return load_quote(db, quote.id)


@router.patch("/quotes/{quote_id}/status", response_model=QuoteRead)
def update_quote_status(
    quote_id: str,
    data: QuoteStatusUpdate,
    db: Session = Depends(get_db),
) -> Quote:
    quote = load_quote(db, quote_id)
    allowed = {
        "DRAFT": {"SENT"},
        "SENT": {"APPROVED", "REJECTED"},
        "REJECTED": {"SENT"},
        "APPROVED": set(),
    }
    if data.status not in allowed.get(quote.status, set()):
        raise HTTPException(status_code=409, detail="Transición de cotización no permitida")
    quote.status = data.status
    _queue_quote_sync(db, quote, f"status:{data.status}")
    if data.status == "APPROVED":
        quote.approved_by = audit_actor(data.actor)
        quote.approved_at = datetime.now(UTC)
    work_order = db.scalar(select(WorkOrder).where(
        WorkOrder.id == quote.work_order_id,
        WorkOrder.organization_id == current_identity().organization_id,
    )) if quote.work_order_id else None
    if work_order:
        work_order.technician_quote = {
            "quote_id": quote.id,
            "quote_number": quote.number,
            "status": quote.status,
            "subtotal": str(quote.subtotal),
            "grand_total": str(quote.total),
        }
    db.add(
        FlowEvent(
            module="QUOTES",
            action=f"QUOTE_{data.status}",
            item_reference=quote.number,
            actor=audit_actor(data.actor),
            result="SUCCESS",
            metadata_json={"work_order_id": quote.work_order_id, "total": str(quote.total)},
        )
    )
    db.commit()
    return load_quote(db, quote.id)


@router.get("/cash-sessions/current", response_model=CashSessionRead | None)
def current_cash_session(db: Session = Depends(get_db)) -> CashSession | None:
    return db.scalar(
        select(CashSession)
        .where(CashSession.organization_id == current_identity().organization_id, CashSession.status == "OPEN")
        .order_by(CashSession.opened_at.desc())
    )


@router.post("/cash-sessions", response_model=CashSessionRead, status_code=201)
def open_cash_session(data: CashSessionOpen, db: Session = Depends(get_db)) -> CashSession:
    require_cashier_code(data.access_code)
    if current_cash_session(db):
        raise HTTPException(status_code=409, detail="Ya existe un turno de caja abierto")
    session = CashSession(organization_id=current_identity().organization_id,
                          branch_id=operational_branch_id(db),
                          opened_by=audit_actor(data.actor), opening_balance=data.opening_balance)
    db.add(session)
    db.flush()
    db.add(
        FlowEvent(
            module="CASHIER",
            action="CASH_SESSION_OPENED",
            item_reference=session.id,
            actor=audit_actor(data.actor),
            result="SUCCESS",
            metadata_json={"opening_balance": str(data.opening_balance)},
        )
    )
    db.commit()
    db.refresh(session)
    return session


@router.post("/cash-sessions/{session_id}/payments", response_model=PaymentRead, status_code=201)
def capture_payment(
    session_id: str,
    data: PaymentCreate,
    db: Session = Depends(get_db),
) -> Payment:
    require_cashier_code(data.access_code)
    organization_id = current_identity().organization_id
    session = db.scalar(select(CashSession).where(CashSession.id == session_id, CashSession.organization_id == organization_id))
    if session is None or session.status != "OPEN":
        raise HTTPException(status_code=409, detail="El turno de caja no está abierto")
    work_order = db.scalar(select(WorkOrder).where(WorkOrder.id == data.work_order_id, WorkOrder.organization_id == organization_id))
    if work_order is None:
        raise HTTPException(status_code=422, detail="La OT no existe")
    quote = load_quote(db, data.quote_id) if data.quote_id else None
    if quote and (quote.work_order_id != work_order.id or quote.status != "APPROVED"):
        raise HTTPException(
            status_code=409, detail="La cotización debe estar aprobada y pertenecer a la OT"
        )
    if data.method in {"CARD", "TRANSFER"} and not data.reference:
        raise HTTPException(status_code=422, detail="Tarjeta y transferencia requieren referencia")
    if quote:
        paid = db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.quote_id == quote.id, Payment.status == "CAPTURED"
            )
        )
        if Decimal(paid) + data.amount > quote.total:
            raise HTTPException(status_code=409, detail="El pago excede el saldo de la cotización")
    payment = Payment(
        organization_id=organization_id,
        branch_id=session.branch_id,
        receipt_number=f"REC-{datetime.now(UTC):%y%m%d}-{uuid.uuid4().hex[:5].upper()}",
        cash_session_id=session.id,
        work_order_id=work_order.id,
        quote_id=quote.id if quote else None,
        method=data.method,
        amount=data.amount,
        reference=data.reference,
        received_by=audit_actor(data.actor),
    )
    db.add(payment)
    db.flush()
    db.add(
        FlowEvent(
            module="CASHIER",
            action="PAYMENT_RECORDED",
            item_reference=payment.receipt_number,
            actor=audit_actor(data.actor),
            result="SUCCESS",
            metadata_json={
                "work_order": work_order.number,
                "method": data.method,
                "amount": str(data.amount),
            },
        )
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/cash-sessions/{session_id}/close", response_model=CashSessionRead)
def close_cash_session(
    session_id: str,
    data: CashSessionClose,
    db: Session = Depends(get_db),
) -> CashSession:
    require_cashier_code(data.access_code)
    session = db.scalar(select(CashSession).where(CashSession.id == session_id, CashSession.organization_id == current_identity().organization_id))
    if session is None or session.status != "OPEN":
        raise HTTPException(status_code=409, detail="El turno de caja no está abierto")
    cash_payments = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.cash_session_id == session.id,
            Payment.method == "CASH",
            Payment.status == "CAPTURED",
        )
    )
    expected = session.opening_balance + Decimal(cash_payments)
    session.expected_cash = expected
    session.counted_cash = data.counted_cash
    session.difference = data.counted_cash - expected
    session.closed_by = audit_actor(data.actor)
    session.closed_at = datetime.now(UTC)
    session.status = "CLOSED"
    db.add(
        FlowEvent(
            module="CASHIER",
            action="CASH_SESSION_CLOSED",
            item_reference=session.id,
            actor=audit_actor(data.actor),
            result="SUCCESS",
            metadata_json={
                "expected_cash": str(expected),
                "counted_cash": str(data.counted_cash),
                "difference": str(session.difference),
            },
        )
    )
    db.commit()
    db.refresh(session)
    return session


@router.get("/cash-summary", response_model=CashSummary)
def cash_summary(db: Session = Depends(get_db)) -> CashSummary:
    session = current_cash_session(db)
    if session is None:
        latest = db.scalar(select(CashSession).where(
            CashSession.organization_id == current_identity().organization_id
        ).order_by(CashSession.opened_at.desc()))
        session = latest
    payments = (
        []
        if session is None
        else list(
            db.scalars(
                select(Payment)
                .where(Payment.cash_session_id == session.id)
                .order_by(Payment.created_at.desc())
            )
        )
    )
    totals = {method: Decimal("0.00") for method in ("CASH", "CARD", "TRANSFER")}
    for payment in payments:
        if payment.status == "CAPTURED":
            totals[payment.method] += payment.amount
    return CashSummary(
        session=session,
        payments=payments,
        totals_by_method=totals,
        total_collected=sum(totals.values(), Decimal("0.00")),
    )
