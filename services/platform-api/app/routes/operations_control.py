from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.request_context import audit_actor, current_identity
from app.db import get_db
from app.models import (
    Branch,
    CatalogProduct,
    ChatSession,
    FlowEvent,
    InventoryReservation,
    InventoryTransfer,
    ManagementDocument,
    QualityCase,
    SalesLead,
    Shipment,
    StaffUser,
    StoreOrder,
    Vehicle,
    VehicleHistoryEvent,
    WarehouseLocation,
    WorkOrder,
)
from app.staff_auth import effective_permissions
from app.services.erp_outbox import enqueue_erp_job
from app.config import Settings, get_settings
from app.services.public_abuse import enforce_public_limit, reject_honeypot
from app.schemas import (
    BranchCreate,
    BranchRead,
    LeadCreate,
    LeadActivityCreate,
    LeadRead,
    LeadUpdate,
    LeadSurveyCreate,
    ManagementDocumentCreate,
    ManagementDocumentRead,
    ManagementDocumentStatusUpdate,
    OperationsOverview,
    QualityCaseCreate,
    QualityCaseRead,
    ReservationCreate,
    ReservationRead,
    ShipmentCreate,
    ShipmentRead,
    StatusActorUpdate,
    TransferCreate,
    TransferRead,
    VehicleHistoryCreate,
    VehicleHistoryRead,
    WarehouseCreate,
    WarehouseRead,
)

public_router = APIRouter(prefix="/api/v1", tags=["sales-leads"])
router = APIRouter(
    prefix="/api/v1/operations/control",
    tags=["operations-control"],
    dependencies=[Depends(require_admin)],
)


def _number(prefix: str) -> str:
    return f"{prefix}-{datetime.now(UTC):%y%m%d}-{uuid.uuid4().hex[:6].upper()}"


def _event(
    module: str,
    action: str,
    reference: str,
    actor: str,
    metadata: dict[str, object] | None = None,
) -> FlowEvent:
    return FlowEvent(
        module=module,
        action=action,
        item_reference=reference,
        actor=actor,
        result="SUCCESS",
        metadata_json=metadata or {},
    )


def _ensure_default_structure(db: Session) -> None:
    identity = current_identity()
    # Bootstrap is an organization-level administrative operation. Scoped
    # employees may read their overview, but a GET from those sessions must
    # never create or mutate shared branches/warehouses.
    if identity.enforce_branch_scope:
        return
    organization_id = identity.organization_id
    # MAIN is an organization-level bootstrap record. A branch-scoped session
    # must be able to see it here, otherwise a harmless GET tries to insert a
    # duplicate branch. The explicit organization predicate keeps the bypass
    # tenant-safe.
    branch = db.scalar(
        select(Branch)
        .where(Branch.organization_id == organization_id, Branch.code == "MAIN")
        .execution_options(include_all_tenants=True)
    )
    if branch is None:
        branch = Branch(
            organization_id=organization_id,
            code="MAIN",
            name="SmartDiag 504 - Sucursal principal",
            address="Tegucigalpa, Honduras",
            phone="+504 0000-0000",
            email_domain="smartdiag504.com",
        )
        db.add(branch)
        db.flush()
    defaults = {
        "MAIN-STOCK": ("Bodega principal", "STOCK"),
        "MAIN-PROCESS": ("Repuestos reservados / proceso", "PROCESS"),
        "MAIN-TRANSIT": ("Bodega en tránsito", "TRANSIT"),
        "MAIN-RETURNS": ("Bodega de devoluciones", "RETURNS"),
    }
    existing = set(
        db.scalars(
            select(WarehouseLocation.code)
            .where(
                WarehouseLocation.organization_id == organization_id,
                WarehouseLocation.code.in_(defaults),
            )
            .execution_options(include_all_tenants=True)
        )
    )
    for code, (name, warehouse_type) in defaults.items():
        if code not in existing:
            db.add(
                WarehouseLocation(
                    organization_id=organization_id,
                    branch_id=branch.id,
                    code=code,
                    name=name,
                    warehouse_type=warehouse_type,
                )
            )
    db.commit()


@public_router.post("/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def capture_lead(
    data: LeadCreate,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SalesLead:
    reject_honeypot(data.website)
    enforce_public_limit(request, settings, surface="lead", limit=settings.public_lead_limit_per_minute)
    return _capture_lead(data, db)


def _capture_lead(data: LeadCreate, db: Session) -> SalesLead:
    if data.chat_session_id and db.get(ChatSession, data.chat_session_id) is None:
        raise HTTPException(status_code=422, detail="La conversación indicada no existe")
    lead = SalesLead(
        number=_number("LEAD"),
        source=data.source,
        full_name=data.full_name.strip(),
        phone=data.phone.strip(),
        email=str(data.email) if data.email else None,
        interest=data.interest.strip(),
        vehicle_summary=data.vehicle_summary.strip() if data.vehicle_summary else None,
        chat_session_id=data.chat_session_id,
    )
    db.add(lead)
    db.flush()
    db.add(
        _event(
            "CRM",
            "LEAD_CAPTURED",
            lead.number,
            "public-ai",
            {"source": lead.source, "has_chat": bool(lead.chat_session_id)},
        )
    )
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/overview", response_model=OperationsOverview)
def overview(
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> OperationsOverview:
    _ensure_default_structure(db)
    permissions = {"*"} if principal is None else effective_permissions(principal)
    organization_id = current_identity().organization_id
    can = lambda permission: "*" in permissions or permission in permissions
    return OperationsOverview(
        branches=list(db.scalars(select(Branch).where(Branch.organization_id == organization_id).order_by(Branch.code))) if can("MANAGEMENT") else [],
        warehouses=list(db.scalars(select(WarehouseLocation).where(WarehouseLocation.organization_id == organization_id).order_by(WarehouseLocation.code))) if can("WAREHOUSE") else [],
        reservations=list(
            db.scalars(
                select(InventoryReservation)
                .where(InventoryReservation.organization_id == organization_id)
                .order_by(InventoryReservation.created_at.desc())
                .limit(50)
            )
        ) if can("WAREHOUSE") else [],
        transfers=list(
            db.scalars(
                select(InventoryTransfer).where(InventoryTransfer.organization_id == organization_id).order_by(InventoryTransfer.created_at.desc()).limit(50)
            )
        ) if can("WAREHOUSE") else [],
        shipments=list(db.scalars(select(Shipment).where(Shipment.organization_id == organization_id).order_by(Shipment.created_at.desc()).limit(50))) if can("WAREHOUSE") else [],
        quality_cases=list(
            db.scalars(select(QualityCase).where(QualityCase.organization_id == organization_id).order_by(QualityCase.created_at.desc()).limit(50))
        ) if can("PROCESSES") else [],
        leads=list(db.scalars(select(SalesLead).where(SalesLead.organization_id == organization_id).order_by(SalesLead.created_at.desc()).limit(100))) if can("CRM") else [],
        management_documents=list(
            db.scalars(
                select(ManagementDocument).where(ManagementDocument.organization_id == organization_id).order_by(ManagementDocument.created_at.desc()).limit(100)
            )
        ) if can("MANAGEMENT") or can("REPORTS") else [],
    )


@router.post("/branches", response_model=BranchRead, status_code=201)
def create_branch(data: BranchCreate, db: Session = Depends(get_db)) -> Branch:
    branch = Branch(**data.model_dump(), organization_id=current_identity().organization_id)
    db.add(branch)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="El código de sucursal ya existe") from exc
    db.refresh(branch)
    return branch


@router.post("/warehouses", response_model=WarehouseRead, status_code=201)
def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db)) -> WarehouseLocation:
    organization_id = current_identity().organization_id
    if db.scalar(select(Branch.id).where(Branch.id == data.branch_id, Branch.organization_id == organization_id)) is None:
        raise HTTPException(status_code=422, detail="La sucursal no existe")
    warehouse = WarehouseLocation(**data.model_dump(), organization_id=organization_id)
    db.add(warehouse)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="El código de bodega ya existe") from exc
    db.refresh(warehouse)
    return warehouse


@router.post("/reservations", response_model=ReservationRead, status_code=201)
def create_reservation(
    data: ReservationCreate, db: Session = Depends(get_db)
) -> InventoryReservation:
    organization_id = current_identity().organization_id
    if db.scalar(select(CatalogProduct.id).where(CatalogProduct.id == data.product_id, CatalogProduct.organization_id == organization_id)) is None:
        raise HTTPException(status_code=422, detail="El repuesto no existe")
    if db.scalar(select(WarehouseLocation.id).where(WarehouseLocation.id == data.warehouse_id, WarehouseLocation.organization_id == organization_id)) is None:
        raise HTTPException(status_code=422, detail="La bodega no existe")
    order = db.scalar(select(StoreOrder).where(StoreOrder.id == data.store_order_id, StoreOrder.organization_id == organization_id)) if data.store_order_id else None
    work_order = db.scalar(select(WorkOrder).where(WorkOrder.id == data.work_order_id, WorkOrder.organization_id == organization_id)) if data.work_order_id else None
    if data.store_order_id and order is None:
        raise HTTPException(status_code=422, detail="El pedido no existe")
    if data.work_order_id and work_order is None:
        raise HTTPException(status_code=422, detail="La OT no existe")
    actual_actor = audit_actor(data.actor)
    reservation = InventoryReservation(
        organization_id=organization_id,
        reference=_number("RES"),
        **data.model_dump(exclude={"actor"}),
        actor=actual_actor,
    )
    db.add(reservation)
    db.flush()
    if order:
        order.status = "RESERVED"
        order.fulfillment_status = "RESERVED"
        order.reservation_expires_at = data.expires_at
    reference = order.order_number if order else work_order.number
    db.add(
        _event(
            "INVENTORY",
            "PART_RESERVED",
            reference,
            actual_actor,
            {"reservation": reservation.reference, "product_id": data.product_id},
        )
    )
    db.commit()
    db.refresh(reservation)
    return reservation


@router.post("/transfers", response_model=TransferRead, status_code=201)
def create_transfer(data: TransferCreate, db: Session = Depends(get_db)) -> InventoryTransfer:
    if data.from_warehouse_id == data.to_warehouse_id:
        raise HTTPException(status_code=422, detail="Origen y destino deben ser diferentes")
    organization_id = current_identity().organization_id
    warehouse_count = db.scalar(select(func.count()).select_from(WarehouseLocation).where(
        WarehouseLocation.organization_id == organization_id,
        WarehouseLocation.id.in_([data.from_warehouse_id, data.to_warehouse_id]),
    )) or 0
    if warehouse_count != 2:
        raise HTTPException(status_code=422, detail="Una de las bodegas no existe")
    actual_actor = audit_actor(data.actor)
    transfer = InventoryTransfer(
        organization_id=organization_id,
        number=_number("MOV"),
        **data.model_dump(exclude={"actor"}),
        actor=actual_actor,
    )
    db.add(transfer)
    db.flush()
    db.add(_event("INVENTORY", "TRANSFER_REQUESTED", transfer.number, actual_actor))
    db.commit()
    db.refresh(transfer)
    return transfer


@router.patch("/transfers/{transfer_id}", response_model=TransferRead)
def update_transfer(
    transfer_id: str, data: StatusActorUpdate, db: Session = Depends(get_db)
) -> InventoryTransfer:
    transfer = db.scalar(select(InventoryTransfer).where(
        InventoryTransfer.id == transfer_id,
        InventoryTransfer.organization_id == current_identity().organization_id,
    ))
    if transfer is None:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    allowed = {"REQUESTED", "PICKED", "IN_TRANSIT", "RECEIVED", "CANCELLED"}
    if data.status not in allowed:
        raise HTTPException(status_code=422, detail="Estado de movimiento no permitido")
    if data.status == "IN_TRANSIT" and not (data.guide_image_url or transfer.guide_image_url):
        raise HTTPException(status_code=422, detail="La guía es obligatoria al salir a tránsito")
    requested_status = data.status
    transfer.status = "ERP_PENDING" if requested_status == "RECEIVED" else requested_status
    transfer.actor = audit_actor(data.actor)
    transfer.tracking_number = data.tracking_number or transfer.tracking_number
    transfer.guide_image_url = data.guide_image_url or transfer.guide_image_url
    if requested_status == "RECEIVED":
        transfer.erp_sync_status = "PENDING"
        transfer.erp_sync_error = None
        enqueue_erp_job(
            db,
            aggregate_type="INVENTORY_TRANSFER",
            aggregate_id=transfer.id,
            operation="SUBMIT_STOCK_TRANSFER",
            idempotency_key=f"inventory-transfer:{transfer.id}:received",
            payload={},
        )
    db.add(_event("INVENTORY", f"TRANSFER_{requested_status}", transfer.number, transfer.actor))
    db.commit()
    db.refresh(transfer)
    return transfer


@router.post("/shipments", response_model=ShipmentRead, status_code=201)
def create_shipment(data: ShipmentCreate, db: Session = Depends(get_db)) -> Shipment:
    organization_id = current_identity().organization_id
    order = db.scalar(select(StoreOrder).where(StoreOrder.id == data.store_order_id, StoreOrder.organization_id == organization_id))
    if order is None:
        raise HTTPException(status_code=422, detail="El pedido no existe")
    if db.scalar(select(WarehouseLocation.id).where(WarehouseLocation.id == data.from_warehouse_id, WarehouseLocation.organization_id == organization_id)) is None:
        raise HTTPException(status_code=422, detail="La bodega no existe")
    actual_actor = audit_actor(data.actor)
    shipment = Shipment(
        organization_id=organization_id,
        number=_number("FLE"),
        **data.model_dump(exclude={"actor"}),
        actor=actual_actor,
    )
    order.status = "PREPARING"
    order.fulfillment_status = "PREPARING"
    db.add(shipment)
    db.flush()
    db.add(
        _event(
            "FREIGHT",
            "SHIPMENT_CREATED",
            shipment.number,
            actual_actor,
            {"order": order.order_number},
        )
    )
    db.commit()
    db.refresh(shipment)
    return shipment


@router.patch("/shipments/{shipment_id}", response_model=ShipmentRead)
def update_shipment(
    shipment_id: str, data: StatusActorUpdate, db: Session = Depends(get_db)
) -> Shipment:
    shipment = db.scalar(select(Shipment).where(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_identity().organization_id,
    ))
    if shipment is None:
        raise HTTPException(status_code=404, detail="Flete no encontrado")
    allowed = {"PREPARING", "READY", "SHIPPED", "DELIVERED", "RETURNED", "CANCELLED"}
    if data.status not in allowed:
        raise HTTPException(status_code=422, detail="Estado de flete no permitido")
    tracking = data.tracking_number or shipment.tracking_number
    guide = data.guide_image_url or shipment.guide_image_url
    if data.status == "SHIPPED" and (not tracking or not guide):
        raise HTTPException(status_code=422, detail="Envío requiere número y foto de guía")
    shipment.status = data.status
    shipment.actor = audit_actor(data.actor)
    shipment.tracking_number = tracking
    shipment.guide_image_url = guide
    order = db.scalar(select(StoreOrder).where(
        StoreOrder.id == shipment.store_order_id,
        StoreOrder.organization_id == current_identity().organization_id,
    ))
    if order:
        order.status = data.status
        order.fulfillment_status = data.status
    db.add(_event("FREIGHT", f"SHIPMENT_{data.status}", shipment.number, shipment.actor))
    db.commit()
    db.refresh(shipment)
    return shipment


@router.post("/quality-cases", response_model=QualityCaseRead, status_code=201)
def create_quality_case(data: QualityCaseCreate, db: Session = Depends(get_db)) -> QualityCase:
    organization_id = current_identity().organization_id
    vehicle = db.scalar(select(Vehicle).where(Vehicle.id == data.vehicle_id, Vehicle.organization_id == organization_id)) if data.vehicle_id else None
    if data.vehicle_id and vehicle is None:
        raise HTTPException(status_code=422, detail="El vehículo no existe")
    actual_actor = audit_actor(data.actor)
    quality = QualityCase(
        organization_id=organization_id,
        number=_number("CAL"),
        **data.model_dump(exclude={"actor"}),
        actor=actual_actor,
    )
    db.add(quality)
    db.flush()
    if vehicle and vehicle.vin:
        db.add(
            VehicleHistoryEvent(
                organization_id=organization_id,
                vehicle_id=vehicle.id,
                vin=vehicle.vin,
                event_type="RETURN" if data.case_type == "RETURN" else "QUALITY",
                reference=quality.number,
                summary=data.description[:500],
                actor=actual_actor,
                metadata_json={"case_type": data.case_type, "status": quality.status},
            )
        )
    db.add(_event("QUALITY", "CASE_OPENED", quality.number, actual_actor, {"type": data.case_type}))
    db.commit()
    db.refresh(quality)
    return quality


@router.patch("/quality-cases/{case_id}", response_model=QualityCaseRead)
def update_quality_case(
    case_id: str, data: StatusActorUpdate, db: Session = Depends(get_db)
) -> QualityCase:
    quality = db.scalar(select(QualityCase).where(
        QualityCase.id == case_id,
        QualityCase.organization_id == current_identity().organization_id,
    ))
    if quality is None:
        raise HTTPException(status_code=404, detail="Caso de calidad no encontrado")
    allowed = {"OPEN", "INSPECTING", "APPROVED", "REJECTED", "RESOLVED", "CLOSED"}
    if data.status not in allowed:
        raise HTTPException(status_code=422, detail="Estado de calidad no permitido")
    if data.status in {"RESOLVED", "CLOSED"} and not data.resolution:
        raise HTTPException(status_code=422, detail="La resolución es obligatoria")
    quality.status = data.status
    quality.actor = audit_actor(data.actor)
    quality.resolution = data.resolution or quality.resolution
    db.add(_event("QUALITY", f"CASE_{data.status}", quality.number, quality.actor))
    db.commit()
    db.refresh(quality)
    return quality


@router.get("/vehicle-history", response_model=list[VehicleHistoryRead])
def vehicle_history(
    vin: str = Query(min_length=5, max_length=40), db: Session = Depends(get_db)
) -> list[VehicleHistoryEvent]:
    return list(
        db.scalars(
            select(VehicleHistoryEvent)
            .where(VehicleHistoryEvent.organization_id == current_identity().organization_id,
                   VehicleHistoryEvent.vin == vin.strip().upper())
            .order_by(VehicleHistoryEvent.created_at.desc())
        )
    )


@router.post("/vehicle-history", response_model=VehicleHistoryRead, status_code=201)
def create_vehicle_history(
    data: VehicleHistoryCreate, db: Session = Depends(get_db)
) -> VehicleHistoryEvent:
    vin = data.vin.strip().upper()
    organization_id = current_identity().organization_id
    vehicle = db.scalar(select(Vehicle).where(Vehicle.organization_id == organization_id, Vehicle.vin == vin))
    event = VehicleHistoryEvent(
        organization_id=organization_id,
        vehicle_id=vehicle.id if vehicle else None, **data.model_dump(exclude={"vin"}), vin=vin
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/leads", response_model=list[LeadRead])
def list_leads(db: Session = Depends(get_db)) -> list[SalesLead]:
    return list(db.scalars(select(SalesLead).where(
        SalesLead.organization_id == current_identity().organization_id
    ).order_by(SalesLead.created_at.desc())))


@router.post("/leads", response_model=LeadRead, status_code=201)
def create_lead_by_staff(data: LeadCreate, db: Session = Depends(get_db)) -> SalesLead:
    return _capture_lead(data, db)


@router.get("/leads/{lead_id}/activities")
def lead_activities(lead_id: str, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    lead = db.scalar(select(SalesLead).where(SalesLead.id == lead_id, SalesLead.organization_id == current_identity().organization_id))
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    events = list(db.scalars(select(FlowEvent).where(FlowEvent.organization_id == current_identity().organization_id, FlowEvent.module == "CRM", FlowEvent.item_reference == lead.number).order_by(FlowEvent.created_at.desc())))
    return [{"id": event.id, "action": event.action, "actor": event.actor,
             "content": event.metadata_json.get("content", ""), "outcome": event.metadata_json.get("outcome"),
             "created_at": event.created_at.isoformat()} for event in events]


@router.post("/leads/{lead_id}/activities", status_code=201)
def create_lead_activity(lead_id: str, data: LeadActivityCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    lead = db.scalar(select(SalesLead).where(SalesLead.id == lead_id, SalesLead.organization_id == current_identity().organization_id))
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    event = _event("CRM", f"ACTIVITY_{data.activity_type}", lead.number, audit_actor(data.actor),
                   {"content": data.content, "outcome": data.outcome})
    db.add(event); db.commit(); db.refresh(event)
    return {"id": event.id, "action": event.action, "actor": event.actor, "content": data.content,
            "outcome": data.outcome, "created_at": event.created_at.isoformat()}


@router.post("/leads/{lead_id}/surveys", status_code=201)
def create_lead_survey(lead_id: str, data: LeadSurveyCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    lead = db.scalar(select(SalesLead).where(SalesLead.id == lead_id, SalesLead.organization_id == current_identity().organization_id))
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    event = _event("CRM", "SURVEY_RECORDED", lead.number, audit_actor(data.actor),
                   {"survey_name": data.survey_name, "answers": data.answers})
    db.add(event); db.commit(); db.refresh(event)
    return {"id": event.id, "lead_id": lead.id, "survey_name": data.survey_name,
            "answers": data.answers, "created_at": event.created_at.isoformat()}


@router.patch("/leads/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: str, data: LeadUpdate, db: Session = Depends(get_db)) -> SalesLead:
    lead = db.scalar(select(SalesLead).where(SalesLead.id == lead_id, SalesLead.organization_id == current_identity().organization_id))
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    previous = lead.status
    lead.status = data.status
    lead.assigned_to = data.assigned_to
    lead.next_action_at = data.next_action_at
    lead.notes = data.notes
    db.add(_event("CRM", f"LEAD_{data.status}", lead.number, audit_actor(data.actor), {"from": previous}))
    db.commit()
    db.refresh(lead)
    return lead


def _validate_fiscal_configuration(data: ManagementDocumentCreate) -> None:
    if data.document_type != "FISCAL_CONFIGURATION":
        return
    mode = str(data.metadata_json.get("numbering_owner") or "")
    if mode not in {"ERPNEXT", "PREPRINTED"}:
        raise HTTPException(status_code=422, detail="Seleccione ERPNext o formulario preimpreso como dueño de la numeración")
    if not str(data.metadata_json.get("legal_name") or "").strip():
        raise HTTPException(status_code=422, detail="La razón social es obligatoria")
    if not str(data.metadata_json.get("rtn") or "").strip():
        raise HTTPException(status_code=422, detail="El RTN es obligatorio")
    if mode == "PREPRINTED":
        start = int(data.metadata_json.get("range_start") or 0)
        end = int(data.metadata_json.get("range_end") or 0)
        if start <= 0 or end < start:
            raise HTTPException(status_code=422, detail="El rango preimpreso no es válido")


@router.post("/management-documents", response_model=ManagementDocumentRead, status_code=201)
def create_management_document(
    data: ManagementDocumentCreate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ManagementDocument:
    organization_id = current_identity().organization_id
    if db.scalar(select(Branch.id).where(Branch.id == data.branch_id, Branch.organization_id == organization_id)) is None:
        raise HTTPException(status_code=422, detail="La sucursal no existe")
    _validate_fiscal_configuration(data)
    if data.status == "ACTIVE":
        raise HTTPException(status_code=422, detail="Guarde como borrador y active después de la revisión del contador")
    document = ManagementDocument(**data.model_dump(), organization_id=organization_id)
    db.add(document)
    db.flush()
    db.add(_event("ACCOUNTING", "FISCAL_CONFIGURATION_CREATED", document.id, audit_actor("accounting"), {"document_type": document.document_type, "branch_id": document.branch_id}))
    db.commit()
    db.refresh(document)
    return document


@router.patch("/management-documents/{document_id}/status", response_model=ManagementDocumentRead)
def update_management_document_status(
    document_id: str,
    data: ManagementDocumentStatusUpdate,
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ManagementDocument:
    document = db.scalar(select(ManagementDocument).where(
        ManagementDocument.id == document_id,
        ManagementDocument.organization_id == current_identity().organization_id,
    ))
    if document is None:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    if data.status == "ACTIVE":
        if not data.accountant_confirmed:
            raise HTTPException(status_code=422, detail="El contador debe confirmar la configuración antes de activarla")
        if document.document_type == "FISCAL_CONFIGURATION":
            for current in db.scalars(
                select(ManagementDocument).where(
                    ManagementDocument.branch_id == document.branch_id,
                    ManagementDocument.document_type == document.document_type,
                    ManagementDocument.status == "ACTIVE",
                    ManagementDocument.id != document.id,
                )
            ):
                current.status = "EXPIRED"
                db.add(current)
            metadata = dict(document.metadata_json or {})
            metadata["accountant_confirmed"] = True
            metadata["accountant_actor"] = audit_actor("accounting")
            metadata["accountant_note"] = data.note or "Revisado desde el módulo de contador"
            metadata["activated_at"] = datetime.now(UTC).isoformat()
            document.metadata_json = metadata
    document.status = data.status
    db.add(document)
    db.add(_event("ACCOUNTING", f"FISCAL_CONFIGURATION_{data.status}", document.id, audit_actor("accounting"), {"branch_id": document.branch_id, "note": data.note or ""}))
    db.commit()
    db.refresh(document)
    return document
