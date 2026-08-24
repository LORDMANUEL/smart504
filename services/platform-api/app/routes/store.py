from __future__ import annotations

import hashlib
import uuid
from io import BytesIO
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from PIL import Image, UnidentifiedImageError

from app.auth import require_admin
from app.db import get_db
from app.models import CatalogProduct, ClientUser, Customer, FlowEvent, StoreOrder, StoreOrderItem, WorkshopSetting
from app.config import get_settings
from app.request_context import current_identity
from app.services.media import read_private_evidence, store_private_evidence
from app.schemas import StoreOrderCreate, StoreOrderRead, StoreOrderStatusUpdate
from app.request_context import audit_actor
from app.services.notifications import enqueue_notification
from app.services.branch_scope import operational_branch_id
from app.services.public_abuse import enforce_public_limit, reject_honeypot
from app.services.pricing import product_pricing_policy, validate_transaction_floor

router = APIRouter(prefix="/api/v1", tags=["store"])
admin_router = APIRouter(
    prefix="/api/v1/admin/store",
    tags=["store-admin"],
    dependencies=[Depends(require_admin)],
)

MONEY = Decimal("0.01")
PDF_ACTIVE_MARKERS = (b"/JavaScript", b"/JS", b"/Launch", b"/EmbeddedFile", b"/OpenAction", b"/AA", b"/RichMedia", b"/XFA")


def _sanitize_payment_proof(raw: bytes, content_type: str) -> bytes:
    if content_type == "application/pdf":
        if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-2048:]:
            raise HTTPException(status_code=422, detail="El archivo no es un PDF completo y válido")
        if any(marker.lower() in raw.lower() for marker in PDF_ACTIVE_MARKERS):
            raise HTTPException(status_code=422, detail="El PDF contiene funciones activas no permitidas")
        return raw
    try:
        with Image.open(BytesIO(raw)) as image:
            image.verify()
        with Image.open(BytesIO(raw)) as image:
            if image.width * image.height > 24_000_000:
                raise HTTPException(status_code=422, detail="La imagen excede la resolución permitida")
            normalized = image.convert("RGB")
            output = BytesIO()
            if content_type == "image/png":
                normalized.save(output, format="PNG", optimize=True)
            else:
                normalized.save(output, format="JPEG", quality=90, optimize=True)
            return output.getvalue()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=422, detail="La imagen no es válida") from exc


def _load_order(db: Session, order_id: str) -> StoreOrder:
    order = db.scalar(
        select(StoreOrder).where(StoreOrder.id == order_id).options(selectinload(StoreOrder.items))
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Store order not found")
    return order


def _generate_order_number() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"WEB-{stamp}-{uuid.uuid4().hex[:8].upper()}"


@admin_router.post("/orders/{order_id}/payment-proofs", status_code=status.HTTP_201_CREATED)
async def upload_payment_proof(
    order_id: str, reference: str = Form(..., min_length=3, max_length=180),
    amount: Decimal = Form(..., gt=0), file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    order = _load_order(db, order_id)
    allowed = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Use PDF, JPG o PNG")
    raw = await file.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El comprobante supera 8 MB")
    raw = _sanitize_payment_proof(raw, file.content_type)
    proof_id = str(uuid.uuid4())
    digest = hashlib.sha256(raw).hexdigest()
    settings = get_settings()
    storage_backend = settings.private_evidence_backend.lower()
    extension = allowed[file.content_type]
    if storage_backend == "s3":
        storage_key = f"payment-proofs/{order.organization_id}/{order.id}/{proof_id}-{digest[:16]}{extension}"
        store_private_evidence(content=raw, object_key=storage_key, mime_type=file.content_type,
                               sha256=digest, settings=settings)
    else:
        folder = settings.private_evidence_root / "payment-proofs" / order.id
        folder.mkdir(parents=True, exist_ok=True)
        storage_key = f"{proof_id}-{digest[:16]}{extension}"
        (folder / storage_key).write_bytes(raw)
    payload: dict[str, object] = {"proof_id": proof_id, "reference": reference.strip(),
        "amount": str(amount.quantize(MONEY)), "mime_type": file.content_type,
        "storage_backend": storage_backend, "storage_key": storage_key,
        "sha256": digest, "uploaded_at": datetime.now(UTC).isoformat()}
    db.add(FlowEvent(module="STORE_PAYMENT", action="PAYMENT_PROOF_UPLOADED",
        item_reference=order.order_number, actor=audit_actor("caja"), result="SUCCESS",
        metadata_json=payload))
    db.commit()
    return {key: value for key, value in payload.items() if key not in {"storage_key", "sha256"}}


@admin_router.get("/orders/{order_id}/payment-proofs")
def list_payment_proofs(order_id: str, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    order = _load_order(db, order_id)
    events = db.scalars(select(FlowEvent).where(
        FlowEvent.organization_id == current_identity().organization_id,
        FlowEvent.module == "STORE_PAYMENT", FlowEvent.item_reference == order.order_number,
        FlowEvent.action == "PAYMENT_PROOF_UPLOADED",
    ).order_by(FlowEvent.created_at.desc())).all()
    return [{key: value for key, value in event.metadata_json.items() if key not in {"storage_key", "sha256"}}
            | {"content_url": f"/api/v1/admin/store/orders/{order.id}/payment-proofs/{event.metadata_json['proof_id']}/content"}
            for event in events]


@admin_router.get("/orders/{order_id}/payment-proofs/{proof_id}/content")
def payment_proof_content(order_id: str, proof_id: str, db: Session = Depends(get_db)) -> Response:
    order = _load_order(db, order_id)
    event = db.scalar(select(FlowEvent).where(
        FlowEvent.organization_id == current_identity().organization_id,
        FlowEvent.module == "STORE_PAYMENT", FlowEvent.item_reference == order.order_number,
        FlowEvent.metadata_json["proof_id"].as_string() == proof_id,
    ))
    if event is None:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    payload = event.metadata_json; settings = get_settings()
    if payload.get("storage_backend") == "s3":
        content = read_private_evidence(object_key=str(payload["storage_key"]), settings=settings)
        return Response(content=content, media_type=str(payload["mime_type"]), headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff", "Content-Disposition": f'attachment; filename="comprobante-{proof_id}"'})
    path = settings.private_evidence_root / "payment-proofs" / order.id / str(payload["storage_key"])
    if not path.is_file(): raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    return FileResponse(path, media_type=str(payload["mime_type"]), headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff", "Content-Disposition": f'attachment; filename="comprobante-{proof_id}"'})


@router.post("/store/orders", response_model=StoreOrderRead, status_code=status.HTTP_201_CREATED)
def create_store_order(
    data: StoreOrderCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> StoreOrder:
    settings = get_settings()
    reject_honeypot(data.website)
    enforce_public_limit(request, settings, surface="store-order", limit=settings.public_order_limit_per_minute)
    existing = db.scalar(
        select(StoreOrder)
        .where(StoreOrder.idempotency_key == data.idempotency_key)
        .options(selectinload(StoreOrder.items))
    )
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return existing

    quantities: dict[str, int] = {}
    for item in data.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
        if quantities[item.product_id] > 20:
            raise HTTPException(status_code=422, detail="Maximum quantity per product is 20")

    products = list(
        db.scalars(
            select(CatalogProduct).where(
                CatalogProduct.id.in_(quantities),
                CatalogProduct.active.is_(True),
            )
        )
    )
    by_id = {product.id: product for product in products}
    missing = sorted(set(quantities) - set(by_id))
    if missing:
        raise HTTPException(status_code=422, detail="One or more products are unavailable")

    currencies = {product.currency for product in products}
    if len(currencies) != 1:
        raise HTTPException(status_code=422, detail="All products must use the same currency")

    subtotal = Decimal("0.00")
    lines: list[StoreOrderItem] = []
    pricing_lines: list[tuple[Decimal, Decimal, Decimal]] = []
    for product_id, quantity in quantities.items():
        product = by_id[product_id]
        if product.stock_status == "OUT_OF_STOCK":
            raise HTTPException(status_code=409, detail=f"El repuesto {product.sku} está agotado")
        if product.stock_status in {"IN_STOCK", "LOW_STOCK"} and product.stock_qty < quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Cantidad no disponible para {product.sku}",
            )
        unit_price = Decimal(product.price).quantize(MONEY, rounding=ROUND_HALF_UP)
        line_total = (unit_price * quantity).quantize(MONEY, rounding=ROUND_HALF_UP)
        subtotal += line_total
        pricing_lines.append((Decimal(quantity), unit_price, product_pricing_policy(product).minimum_sale_price))
        lines.append(
            StoreOrderItem(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    promo_code = data.promo_code.strip().upper() if data.promo_code else None
    discount = Decimal("0.00")
    if promo_code:
        setting = db.get(WorkshopSetting, "marketing_campaigns")
        today = datetime.now(UTC).date().isoformat()
        campaign = next((item for item in (setting.value.get("items", []) if setting else [])
                         if str(item.get("promo_code") or "").upper() == promo_code
                         and item.get("status") == "PUBLISHED"
                         and (not item.get("valid_from") or str(item["valid_from"]) <= today)
                         and (not item.get("valid_until") or str(item["valid_until"]) >= today)), None)
        if campaign is None:
            raise HTTPException(status_code=422, detail="El código promocional no existe o no está vigente")
        discount = (subtotal * Decimal(str(campaign.get("discount_percent") or 0)) / Decimal("100")).quantize(MONEY, rounding=ROUND_HALF_UP)
        validate_transaction_floor(lines=pricing_lines, discount=discount)

    order = StoreOrder(
        order_number=_generate_order_number(),
        customer_name=data.customer_name.strip(),
        phone=data.phone.strip(),
        email=str(data.email) if data.email else None,
        vehicle_vin=data.vehicle_vin.strip().upper() if data.vehicle_vin else None,
        notes=data.notes.strip() if data.notes else None,
        status="PENDING_CONFIRMATION",
        currency=next(iter(currencies)),
        subtotal=subtotal.quantize(MONEY, rounding=ROUND_HALF_UP),
        discount=discount,
        total=(subtotal - discount).quantize(MONEY, rounding=ROUND_HALF_UP),
        promo_code=promo_code,
        idempotency_key=data.idempotency_key,
        source="WEB",
        branch_id=operational_branch_id(db),
        assigned_cashier="Caja principal",
        customer_id=db.scalar(
            select(Customer.id).where(
                Customer.email == str(data.email)
                if data.email
                else Customer.phone == data.phone.strip()
            )
        ),
        items=lines,
    )
    db.add(order)
    db.flush()
    db.add(
        FlowEvent(
            module="STORE",
            action="ORDER_CREATED",
            item_reference=order.order_number,
            actor="cliente-web",
            result="SUCCESS",
            metadata_json={
                "fulfillment_status": order.fulfillment_status,
                "assigned_cashier": order.assigned_cashier,
                "outside_business_hours_notice": True,
                "promo_code": promo_code,
                "discount": str(discount),
            },
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        replay = db.scalar(
            select(StoreOrder)
            .where(StoreOrder.idempotency_key == data.idempotency_key)
            .options(selectinload(StoreOrder.items))
        )
        if replay is None:
            raise HTTPException(status_code=409, detail="Order could not be created") from exc
        response.status_code = status.HTTP_200_OK
        return replay
    return _load_order(db, order.id)


@admin_router.get("/orders", response_model=list[StoreOrderRead])
def list_store_orders(db: Session = Depends(get_db)) -> list[StoreOrder]:
    return list(
        db.scalars(
            select(StoreOrder)
            .options(selectinload(StoreOrder.items))
            .order_by(StoreOrder.created_at.desc())
        ).unique()
    )


@admin_router.patch("/orders/{order_id}", response_model=StoreOrderRead)
def update_store_order(
    order_id: str,
    data: StoreOrderStatusUpdate,
    db: Session = Depends(get_db),
) -> StoreOrder:
    order = _load_order(db, order_id)
    if data.status == "SYNCED" and not data.erpnext_sales_order_id:
        raise HTTPException(
            status_code=422,
            detail="erpnext_sales_order_id is required when status is SYNCED",
        )
    transitions = {
        "PENDING_CONFIRMATION": {"CONTACTED", "CONFIRMED", "NO_RESPONSE", "LOST", "CANCELLED"},
        "CONTACTED": {"CONFIRMED", "NO_RESPONSE", "LOST", "CANCELLED"},
        "NO_RESPONSE": {"CONTACTED", "LOST", "CANCELLED"},
        "CONFIRMED": {"PAID", "RESERVED", "PREPARING", "SYNCED", "LOST", "CANCELLED"},
        "PAID": {"RESERVED", "PREPARING", "SHIPPED", "RETURN_REQUESTED"},
        "RESERVED": {"PREPARING", "CANCELLED", "RETURN_REQUESTED"},
        "PREPARING": {"SHIPPED", "CANCELLED", "RETURN_REQUESTED"},
        "SHIPPED": {"DELIVERED", "RETURN_REQUESTED"},
        "DELIVERED": {"RETURN_REQUESTED"},
        "RETURN_REQUESTED": {"RETURNED", "CANCELLED"},
        "RETURNED": set(),
        "SYNCED": {"PREPARING", "SHIPPED", "DELIVERED", "RETURN_REQUESTED"},
        "LOST": set(),
        "CANCELLED": set(),
    }
    if data.status != order.status and data.status not in transitions.get(order.status, set()):
        raise HTTPException(status_code=409, detail="Transición de pedido no permitida")
    previous = order.status
    order.status = data.status
    if data.status in {"PAID", "RESERVED", "PREPARING", "SHIPPED", "DELIVERED", "RETURNED"}:
        order.fulfillment_status = data.status
    if data.erpnext_sales_order_id is not None:
        order.erpnext_sales_order_id = data.erpnext_sales_order_id.strip()
    if data.assigned_cashier is not None:
        order.assigned_cashier = data.assigned_cashier.strip()
    if data.whatsapp_status is not None:
        order.whatsapp_status = data.whatsapp_status
    db.add(
        FlowEvent(
            module="STORE",
            action=f"ORDER_{data.status}",
            item_reference=order.order_number,
            actor=audit_actor(data.actor),
            result="CANCELLED" if data.status == "CANCELLED" else "SUCCESS",
            metadata_json={"from": previous, "whatsapp_status": order.whatsapp_status},
        )
    )
    if order.email:
        message = f"El estado de su pedido cambio de {previous} a {data.status}."
        enqueue_notification(
            db,
            channel="EMAIL",
            recipient=order.email,
            subject=f"Pedido {order.order_number}: {data.status}",
            body_text=message,
            template_key=f"STORE_ORDER_{data.status}",
            aggregate_type="STORE_ORDER",
            aggregate_id=order.id,
            idempotency_key=f"store-order:{order.id}:{data.status}:email",
        )
        db.add(
            FlowEvent(
                module="NOTIFICATIONS",
                action=f"STORE_ORDER_{data.status}",
                item_reference=order.order_number,
                actor=audit_actor(data.actor),
                result="SUCCESS",
                metadata_json={
                    "recipient": order.email,
                    "channel": "EMAIL",
                    "delivery_status": "PENDING",
                    "title": f"Pedido {order.order_number}: {data.status}",
                    "message": message,
                },
            )
        )
    if order.phone:
        enqueue_notification(
            db,
            channel="WHATSAPP",
            recipient=order.phone,
            subject=None,
            body_text=f"SmartDiag504: su pedido {order.order_number} cambio a {data.status}.",
            template_key=f"STORE_ORDER_{data.status}",
            aggregate_type="STORE_ORDER",
            aggregate_id=order.id,
            idempotency_key=f"store-order:{order.id}:{data.status}:whatsapp",
        )
    if data.status == "PAID" and previous != "PAID" and order.customer_id:
        client = db.scalar(select(ClientUser).where(ClientUser.customer_id == order.customer_id, ClientUser.organization_id == order.organization_id))
        already_awarded = db.scalar(select(FlowEvent.id).where(FlowEvent.module == "LOYALTY", FlowEvent.action == "POINTS_EARNED", FlowEvent.item_reference == order.order_number))
        if client is not None and client.loyalty_enabled and not already_awarded:
            earned = max(1, int(Decimal(order.total) // Decimal("10")))
            client.loyalty_points += earned
            db.add(FlowEvent(module="LOYALTY", action="POINTS_EARNED", item_reference=order.order_number, actor=audit_actor(data.actor), result="SUCCESS", metadata_json={"points": earned, "balance": client.loyalty_points, "rule": "1_POINT_PER_HNL_10"}))
    db.commit()
    return _load_order(db, order.id)
