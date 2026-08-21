from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db import get_db
from app.models import (
    AttendanceEntry,
    EmployeeContract,
    FlowEvent,
    ImportCase,
    LeaveRequest,
    PayrollRun,
    PayrollPolicy,
    PayrollVoucher,
    PurchaseOrder,
    SocialChannel,
    SocialConversation,
    SocialMessage,
    Supplier,
    StaffUser,
    UsedVehicle,
)
from app.request_context import audit_actor, current_identity
from app.schemas import (
    AttendanceCreate,
    AttendanceRead,
    EmployeeContractCreate,
    EmployeeContractRead,
    EmployeeContractUpdate,
    EnterpriseOverview,
    EnterpriseStatusUpdate,
    ImportCaseCreate,
    ImportCaseRead,
    ImportCaseUpdate,
    OvertimeDecision,
    LeaveRequestCreate,
    LeaveRequestRead,
    PayrollRunCreate,
    PayrollRunRead,
    PayrollPolicyCreate,
    PayrollPolicyRead,
    PayrollVoucherRead,
    PrestationsPreviewCreate,
    PrestationsPreviewRead,
    PurchaseOrderCreate,
    PurchaseOrderRead,
    PurchaseReceiptCreate,
    SocialChannelCreate,
    SocialChannelRead,
    SocialConversationCreate,
    SocialConversationRead,
    SocialMessageCreate,
    SocialMessageRead,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
    UsedVehicleCreate,
    UsedVehicleRead,
)
from app.services.erp_outbox import enqueue_erp_job
from app.services.branch_scope import operational_branch_id
from app.services.notifications import enqueue_notification
from app.staff_auth import effective_permissions


router = APIRouter(
    prefix="/api/v1/operations/enterprise",
    tags=["enterprise-operations"],
    dependencies=[Depends(require_admin)],
)


def _number(prefix: str) -> str:
    return f"{prefix}-{datetime.now(UTC):%y%m%d-%H%M%S%f}"[:32]


def _event(db: Session, module: str, action: str, reference: str, metadata: dict[str, object] | None = None) -> None:
    db.add(FlowEvent(organization_id=current_identity().organization_id, module=module, action=action, item_reference=reference, actor=audit_actor(), result="SUCCESS", metadata_json=metadata or {}))


def _commit(db: Session, duplicate_message: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=duplicate_message) from exc


def _next_employee_code(db: Session, organization_id: str) -> str:
    codes = db.scalars(select(EmployeeContract.employee_code).where(EmployeeContract.organization_id == organization_id, EmployeeContract.employee_code.like("EMP-%"))).all()
    sequence = max((int(code.removeprefix("EMP-")) for code in codes if code.removeprefix("EMP-").isdigit()), default=0) + 1
    return f"EMP-{sequence:06d}"


def _active_payroll_policies(db: Session, organization_id: str, effective_on: date) -> list[PayrollPolicy]:
    return list(db.scalars(select(PayrollPolicy).where(
        PayrollPolicy.organization_id == organization_id,
        PayrollPolicy.active.is_(True),
        PayrollPolicy.effective_from <= effective_on,
        (PayrollPolicy.effective_until.is_(None) | (PayrollPolicy.effective_until >= effective_on)),
    ).order_by(PayrollPolicy.effective_from.desc())))


def _rule_amount(rule: dict[str, object], gross: Decimal) -> Decimal:
    if not rule.get("enabled", True):
        return Decimal("0")
    rate = Decimal(str(rule.get("rate", 0)))
    if rule.get("calculation") == "FIXED":
        return rate.quantize(Decimal("0.01"))
    base = min(gross, Decimal(str(rule["ceiling"]))) if rule.get("ceiling") is not None else gross
    return (base * rate / Decimal("100")).quantize(Decimal("0.01"))


def _period_base(contract: EmployeeContract, period_start: date, period_end: date, regular_hours: Decimal, worked_days: int) -> Decimal:
    period_days = Decimal(str((period_end - period_start).days + 1))
    rate = contract.base_pay_amount or contract.monthly_salary
    divisors = {"MONTHLY": Decimal("30"), "BIWEEKLY": Decimal("15"), "WEEKLY": Decimal("7")}
    if contract.payment_type in divisors:
        divisor = divisors[contract.payment_type]
        return (rate * min(period_days, divisor) / divisor).quantize(Decimal("0.01"))
    if contract.payment_type == "DAILY":
        return (rate * Decimal(worked_days)).quantize(Decimal("0.01"))
    if contract.payment_type == "HOURLY":
        return (rate * regular_hours).quantize(Decimal("0.01"))
    return contract.monthly_salary.quantize(Decimal("0.01"))


@router.get("/overview", response_model=EnterpriseOverview)
def overview(
    principal: StaffUser | None = Depends(require_admin),
    db: Session = Depends(get_db),
) -> EnterpriseOverview:
    org = current_identity().organization_id
    permissions = {"*"} if principal is None else effective_permissions(principal)
    def can(permission: str) -> bool:
        return "*" in permissions or permission in permissions
    suppliers = list(db.scalars(select(Supplier).where(Supplier.organization_id == org).order_by(Supplier.name))) if can("PROCUREMENT") else []
    purchases = list(db.scalars(select(PurchaseOrder).where(PurchaseOrder.organization_id == org).order_by(PurchaseOrder.created_at.desc()).limit(200))) if can("PROCUREMENT") else []
    imports = list(db.scalars(select(ImportCase).where(ImportCase.organization_id == org).order_by(ImportCase.created_at.desc()).limit(200))) if can("PROCUREMENT") else []
    contracts = list(db.scalars(select(EmployeeContract).where(EmployeeContract.organization_id == org).order_by(EmployeeContract.employee_name))) if can("HR") else []
    attendance = list(db.scalars(select(AttendanceEntry).where(AttendanceEntry.organization_id == org).order_by(AttendanceEntry.work_date.desc()).limit(300))) if can("HR") else []
    leave = list(db.scalars(select(LeaveRequest).where(LeaveRequest.organization_id == org).order_by(LeaveRequest.created_at.desc()).limit(200))) if can("HR") else []
    payroll = list(db.scalars(select(PayrollRun).where(PayrollRun.organization_id == org).order_by(PayrollRun.period_start.desc()).limit(100))) if can("HR") else []
    used = list(db.scalars(select(UsedVehicle).where(UsedVehicle.organization_id == org).order_by(UsedVehicle.created_at.desc()).limit(200))) if can("USED_VEHICLES") else []
    channels = list(db.scalars(select(SocialChannel).where(SocialChannel.organization_id == org).order_by(SocialChannel.name))) if can("SOCIAL") else []
    conversations = list(db.scalars(select(SocialConversation).where(SocialConversation.organization_id == org).order_by(SocialConversation.last_message_at.desc()).limit(300))) if can("SOCIAL") else []
    counts = {
        "suppliers": len(suppliers), "purchase_orders": len(purchases), "import_cases": len(imports),
        "contracts": len(contracts), "attendance": len(attendance), "leave_requests": len(leave),
        "payroll_runs": len(payroll), "used_vehicles": len(used), "social_channels": len(channels),
        "social_conversations": len(conversations),
    }
    return EnterpriseOverview(
        counts=counts, suppliers=suppliers, purchase_orders=purchases, import_cases=imports,
        contracts=contracts, attendance=attendance, leave_requests=leave, payroll_runs=payroll,
        used_vehicles=used, social_channels=channels, social_conversations=conversations,
    )


@router.post("/suppliers", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)) -> Supplier:
    values = data.model_dump()
    values.update(code=data.code.upper(), currency=data.currency.upper())
    supplier = Supplier(**values, organization_id=current_identity().organization_id)
    db.add(supplier); db.flush()
    enqueue_erp_job(db, aggregate_type="SUPPLIER", aggregate_id=supplier.id, operation="UPSERT_SUPPLIER", idempotency_key=f"supplier:{supplier.id}:v1", payload={})
    _event(db, "PROCUREMENT", "SUPPLIER_CREATED", supplier.code)
    _commit(db, "Ya existe un proveedor con ese codigo")
    db.refresh(supplier)
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierRead)
def update_supplier(supplier_id: str, data: SupplierUpdate, db: Session = Depends(get_db)) -> Supplier:
    supplier = db.scalar(select(Supplier).where(Supplier.id == supplier_id, Supplier.organization_id == current_identity().organization_id))
    if supplier is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value.upper() if field == "currency" and value else value)
    supplier.erp_sync_status = "PENDING"
    enqueue_erp_job(db, aggregate_type="SUPPLIER", aggregate_id=supplier.id, operation="UPSERT_SUPPLIER", idempotency_key=f"supplier:{supplier.id}:update:{datetime.now(UTC).isoformat()}", payload={})
    _event(db, "PROCUREMENT", "SUPPLIER_UPDATED", supplier.code)
    db.commit(); db.refresh(supplier)
    return supplier


@router.post("/purchase-orders", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
def create_purchase_order(data: PurchaseOrderCreate, db: Session = Depends(get_db)) -> PurchaseOrder:
    if db.scalar(select(Supplier.id).where(Supplier.id == data.supplier_id, Supplier.organization_id == current_identity().organization_id, Supplier.active.is_(True))) is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    items = [item.model_dump(mode="json") for item in data.items]
    subtotal = sum((item.quantity * item.unit_cost for item in data.items), Decimal("0"))
    order = PurchaseOrder(
        organization_id=current_identity().organization_id,
        number=_number("OC"), supplier_id=data.supplier_id, branch_id=operational_branch_id(db, data.branch_id),
        currency=data.currency.upper(), exchange_rate=data.exchange_rate, expected_at=data.expected_at, notes=data.notes, items_json=items,
        subtotal=subtotal, tax=data.tax, total=subtotal + data.tax, created_by=audit_actor(),
    )
    db.add(order); db.flush(); _event(db, "PROCUREMENT", "PURCHASE_ORDER_CREATED", order.number, {"total": str(order.total)})
    db.commit(); db.refresh(order)
    return order


@router.patch("/purchase-orders/{order_id}/status", response_model=PurchaseOrderRead)
def update_purchase_order(order_id: str, data: EnterpriseStatusUpdate, db: Session = Depends(get_db)) -> PurchaseOrder:
    order = db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == order_id, PurchaseOrder.organization_id == current_identity().organization_id))
    if order is None: raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    transitions = {"DRAFT": {"SUBMITTED", "CANCELLED"}, "SUBMITTED": {"APPROVED", "CANCELLED"}, "APPROVED": {"PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED"}, "PARTIALLY_RECEIVED": {"RECEIVED", "CANCELLED"}, "RECEIVED": {"CLOSED"}}
    if data.status not in transitions.get(order.status, set()):
        raise HTTPException(status_code=409, detail=f"No se permite {order.status} -> {data.status}")
    previous = order.status; order.status = data.status
    if data.status in {"SUBMITTED", "APPROVED", "PARTIALLY_RECEIVED", "RECEIVED"}:
        order.erp_sync_status = "PENDING"
        enqueue_erp_job(db, aggregate_type="PURCHASE_ORDER", aggregate_id=order.id, operation="UPSERT_PURCHASE_ORDER", idempotency_key=f"purchase-order:{order.id}:{data.status}", payload={})
    _event(db, "PROCUREMENT", f"PURCHASE_ORDER_{data.status}", order.number, {"from": previous})
    db.commit(); db.refresh(order)
    return order


@router.post("/purchase-orders/{order_id}/receipts", response_model=PurchaseOrderRead)
def receive_purchase_order(order_id: str, data: PurchaseReceiptCreate, db: Session = Depends(get_db)) -> PurchaseOrder:
    order = db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == order_id, PurchaseOrder.organization_id == current_identity().organization_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    if order.status not in {"APPROVED", "PARTIALLY_RECEIVED"}:
        raise HTTPException(status_code=409, detail="La orden debe estar aprobada para recibir mercancia")
    receipt = {item.sku: item.quantity for item in data.items}
    updated: list[dict[str, object]] = []
    for raw in order.items_json:
        item = dict(raw)
        sku = str(item.get("sku", ""))
        ordered = Decimal(str(item.get("quantity", 0)))
        previous = Decimal(str(item.get("received_quantity", 0)))
        incoming = receipt.pop(sku, Decimal("0"))
        if previous + incoming > ordered:
            raise HTTPException(status_code=422, detail=f"La recepcion de {sku} supera la cantidad ordenada")
        item["received_quantity"] = str(previous + incoming)
        updated.append(item)
    if receipt:
        raise HTTPException(status_code=422, detail=f"SKU no incluido en la orden: {next(iter(receipt))}")
    order.items_json = updated
    complete = all(Decimal(str(item.get("received_quantity", 0))) == Decimal(str(item.get("quantity", 0))) for item in updated)
    order.status = "RECEIVED" if complete else "PARTIALLY_RECEIVED"
    order.erp_sync_status = "PENDING"
    enqueue_erp_job(db, aggregate_type="PURCHASE_ORDER", aggregate_id=order.id, operation="UPSERT_PURCHASE_ORDER", idempotency_key=f"purchase-receipt:{order.id}:{data.reference}", payload={"receipt_reference": data.reference, "items": [item.model_dump(mode="json") for item in data.items], "note": data.note})
    _event(db, "PROCUREMENT", "PURCHASE_RECEIPT_RECORDED", order.number, {"reference": data.reference, "complete": complete})
    db.commit(); db.refresh(order)
    return order


@router.post("/import-cases", response_model=ImportCaseRead, status_code=status.HTTP_201_CREATED)
def create_import_case(data: ImportCaseCreate, db: Session = Depends(get_db)) -> ImportCase:
    if db.scalar(select(PurchaseOrder.id).where(PurchaseOrder.id == data.purchase_order_id, PurchaseOrder.organization_id == current_identity().organization_id)) is None:
        raise HTTPException(status_code=404, detail="Orden de compra no encontrada")
    costs = [item.model_dump(mode="json") for item in data.costs]
    total = sum((item.amount for item in data.costs), Decimal("0"))
    case = ImportCase(organization_id=current_identity().organization_id, number=_number("IMP"), purchase_order_id=data.purchase_order_id, incoterm=data.incoterm.upper(),
        origin_country=data.origin_country, destination_port=data.destination_port, eta=data.eta,
        costs_json=costs, documents_json=data.documents, additional_cost_total=total,
        allocation_method=data.allocation_method, created_by=audit_actor())
    db.add(case); db.flush(); _event(db, "IMPORTS", "IMPORT_CASE_CREATED", case.number, {"additional_cost": str(total)})
    db.commit(); db.refresh(case)
    return case


@router.patch("/import-cases/{case_id}", response_model=ImportCaseRead)
def update_import_case_details(case_id: str, data: ImportCaseUpdate, db: Session = Depends(get_db)) -> ImportCase:
    case = db.scalar(select(ImportCase).where(ImportCase.id == case_id, ImportCase.organization_id == current_identity().organization_id))
    if case is None:
        raise HTTPException(status_code=404, detail="Expediente de importacion no encontrado")
    if case.status in {"ALLOCATED", "CANCELLED"}:
        raise HTTPException(status_code=409, detail="El expediente cerrado no puede modificarse")
    if data.eta is not None: case.eta = data.eta
    if data.allocation_method is not None: case.allocation_method = data.allocation_method
    if data.costs is not None:
        case.costs_json = [item.model_dump(mode="json") for item in data.costs]
        case.additional_cost_total = sum((item.amount for item in data.costs), Decimal("0"))
    if data.documents is not None: case.documents_json = data.documents
    _event(db, "IMPORTS", "IMPORT_CASE_UPDATED", case.number)
    db.commit(); db.refresh(case)
    return case


@router.patch("/import-cases/{case_id}/status", response_model=ImportCaseRead)
def update_import_case(case_id: str, data: EnterpriseStatusUpdate, db: Session = Depends(get_db)) -> ImportCase:
    case = db.scalar(select(ImportCase).where(ImportCase.id == case_id, ImportCase.organization_id == current_identity().organization_id))
    if case is None: raise HTTPException(status_code=404, detail="Expediente de importacion no encontrado")
    transitions = {"PLANNED": {"IN_TRANSIT", "CANCELLED"}, "IN_TRANSIT": {"CUSTOMS", "CANCELLED"}, "CUSTOMS": {"RECEIVED", "CANCELLED"}, "RECEIVED": {"ALLOCATED"}}
    if data.status not in transitions.get(case.status, set()): raise HTTPException(status_code=409, detail="Transicion de importacion no permitida")
    case.status = data.status
    if data.status == "ALLOCATED":
        case.landed_cost_status = "ERP_PENDING"
        enqueue_erp_job(db, aggregate_type="IMPORT_CASE", aggregate_id=case.id, operation="SUBMIT_LANDED_COST", idempotency_key=f"import:{case.id}:landed-cost", payload={})
    _event(db, "IMPORTS", f"IMPORT_CASE_{data.status}", case.number)
    db.commit(); db.refresh(case)
    return case


@router.post("/hr/contracts", response_model=EmployeeContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(data: EmployeeContractCreate, db: Session = Depends(get_db)) -> EmployeeContract:
    org = current_identity().organization_id
    values = data.model_dump(exclude={"benefits", "schedule", "branch_id", "employee_code", "base_pay_amount", "staff_user_id"})
    staff_user_id = data.staff_user_id
    linked_staff = None
    if staff_user_id is not None:
        linked_staff = db.scalar(select(StaffUser).where(StaffUser.organization_id == org, StaffUser.id == staff_user_id))
    if staff_user_id is None and data.email:
        linked_staff = db.scalar(select(StaffUser).where(StaffUser.organization_id == org, StaffUser.email == str(data.email).lower()))
        staff_user_id = linked_staff.id if linked_staff else None
    employee_code = data.employee_code or (linked_staff.employee_code if linked_staff else None)
    if employee_code:
        code_owner = db.scalar(select(EmployeeContract.id).where(
            EmployeeContract.organization_id == org,
            EmployeeContract.employee_code == employee_code.upper(),
        ))
        if code_owner is not None and data.employee_code is None:
            employee_code = None
    employee_code = employee_code or _next_employee_code(db, org)
    contract = EmployeeContract(**values, organization_id=org, benefits_json=data.benefits, schedule_json=data.schedule,
        branch_id=operational_branch_id(db, data.branch_id), employee_code=employee_code.upper(),
        base_pay_amount=data.base_pay_amount or data.monthly_salary, staff_user_id=staff_user_id)
    db.add(contract); db.flush()
    enqueue_erp_job(db, aggregate_type="EMPLOYEE_CONTRACT", aggregate_id=contract.id, operation="UPSERT_EMPLOYEE", idempotency_key=f"employee:{contract.id}:v1", payload={})
    _event(db, "HR", "CONTRACT_CREATED", contract.employee_code)
    _commit(db, "Ya existe un contrato para ese codigo de empleado")
    db.refresh(contract)
    return contract


@router.patch("/hr/contracts/{contract_id}", response_model=EmployeeContractRead)
def update_contract(contract_id: str, data: EmployeeContractUpdate, db: Session = Depends(get_db)) -> EmployeeContract:
    contract = db.scalar(select(EmployeeContract).where(EmployeeContract.id == contract_id, EmployeeContract.organization_id == current_identity().organization_id))
    if contract is None:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    values = data.model_dump(exclude_unset=True, exclude={"benefits", "schedule"})
    for field, value in values.items(): setattr(contract, field, value.upper() if field == "currency" and value else value)
    if data.monthly_salary is not None and data.base_pay_amount is None and contract.payment_type == "MONTHLY":
        contract.base_pay_amount = data.monthly_salary
    if data.benefits is not None: contract.benefits_json = data.benefits
    if data.schedule is not None: contract.schedule_json = data.schedule
    contract.erp_sync_status = "PENDING"
    enqueue_erp_job(db, aggregate_type="EMPLOYEE_CONTRACT", aggregate_id=contract.id, operation="UPSERT_EMPLOYEE", idempotency_key=f"employee:{contract.id}:update:{datetime.now(UTC).isoformat()}", payload={})
    _event(db, "HR", "CONTRACT_UPDATED", contract.employee_code)
    db.commit(); db.refresh(contract)
    return contract


@router.get("/hr/payroll-policies", response_model=list[PayrollPolicyRead])
def list_payroll_policies(db: Session = Depends(get_db)) -> list[PayrollPolicy]:
    return list(db.scalars(select(PayrollPolicy).where(PayrollPolicy.organization_id == current_identity().organization_id).order_by(PayrollPolicy.effective_from.desc())))


@router.post("/hr/payroll-policies", response_model=PayrollPolicyRead, status_code=status.HTTP_201_CREATED)
def create_payroll_policy(data: PayrollPolicyCreate, db: Session = Depends(get_db)) -> PayrollPolicy:
    policy = PayrollPolicy(organization_id=current_identity().organization_id, code=data.code.upper(), name=data.name,
        effective_from=data.effective_from, effective_until=data.effective_until,
        rules_json=[rule.model_dump(mode="json") for rule in data.rules], source_reference=data.source_reference,
        approved_by=audit_actor(), active=data.active)
    db.add(policy); _event(db, "HR", "PAYROLL_POLICY_CREATED", policy.code, {"effective_from": policy.effective_from.isoformat()})
    _commit(db, "Ya existe una política con ese código y fecha de vigencia"); db.refresh(policy)
    return policy


@router.get("/hr/payroll-vouchers", response_model=list[PayrollVoucherRead])
def list_payroll_vouchers(contract_id: str | None = None, db: Session = Depends(get_db)) -> list[PayrollVoucher]:
    identity = current_identity()
    query = select(PayrollVoucher).where(PayrollVoucher.organization_id == identity.organization_id)
    if identity.enforce_branch_scope:
        query = query.join(EmployeeContract, EmployeeContract.id == PayrollVoucher.contract_id).where(
            EmployeeContract.organization_id == identity.organization_id,
            EmployeeContract.branch_id == identity.branch_id,
        )
    if contract_id:
        query = query.where(PayrollVoucher.contract_id == contract_id)
    return list(db.scalars(query.order_by(PayrollVoucher.period_end.desc()).limit(500)))


@router.post("/hr/prestations/preview", response_model=PrestationsPreviewRead)
def preview_prestations(data: PrestationsPreviewCreate, db: Session = Depends(get_db)) -> PrestationsPreviewRead:
    contract = db.scalar(select(EmployeeContract).where(EmployeeContract.id == data.contract_id, EmployeeContract.organization_id == current_identity().organization_id))
    if contract is None:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if data.termination_date < contract.start_date:
        raise HTTPException(status_code=422, detail="La fecha de terminación es anterior al inicio laboral")
    service_days = (data.termination_date - contract.start_date).days + 1
    service_years = Decimal(service_days) / Decimal("365")
    daily = (data.average_ordinary_monthly / Decimal("30")).quantize(Decimal("0.01"))
    if service_days < 90: notice_days = Decimal("1")
    elif service_days < 180: notice_days = Decimal("7")
    elif service_days < 365: notice_days = Decimal("14")
    elif service_days < 730: notice_days = Decimal("30")
    else: notice_days = Decimal("60")
    if service_days < 90: severance_days = Decimal("0")
    elif service_days < 180: severance_days = Decimal("10")
    elif service_days < 365: severance_days = Decimal("20")
    else: severance_days = min(Decimal("450"), service_years * Decimal("30"))
    completed_years = service_days // 365
    vacation_entitlement = Decimal("10" if completed_years < 2 else "12" if completed_years < 3 else "15" if completed_years < 4 else "20")
    current_cycle_days = service_days % 365
    divisor = Decimal("36" if completed_years < 1 else "30" if completed_years < 2 else "24" if completed_years < 3 else "18")
    vacation_days = min(vacation_entitlement, Decimal(current_cycle_days) / divisor).quantize(Decimal("0.01"))
    annual_accrual = (data.average_ordinary_monthly * Decimal(current_cycle_days) / Decimal("360")).quantize(Decimal("0.01"))
    notice_amount = (daily * notice_days if data.include_notice else Decimal("0")).quantize(Decimal("0.01"))
    severance_amount = (daily * severance_days if data.include_severance else Decimal("0")).quantize(Decimal("0.01"))
    vacation_amount = (daily * vacation_days).quantize(Decimal("0.01"))
    total = notice_amount + severance_amount + vacation_amount + annual_accrual + annual_accrual
    return PrestationsPreviewRead(employee_code=contract.employee_code, service_days=service_days, daily_average=daily,
        notice_days=notice_days, severance_days=severance_days.quantize(Decimal("0.01")), vacation_days=vacation_days,
        notice_amount=notice_amount, severance_amount=severance_amount, vacation_amount=vacation_amount,
        thirteenth_accrual=annual_accrual, fourteenth_accrual=annual_accrual, estimated_total=total.quantize(Decimal("0.01")),
        legal_notice="Estimación de apoyo basada en la guía SETRASS y los artículos 116, 120, 345, 346, 349 y 352. El contador debe validar causa, salario promedio de seis meses, especie, extras, pagos previos y vigencia antes de liquidar.")


@router.post("/hr/contracts/{contract_id}/terminate", response_model=EmployeeContractRead)
def terminate_contract(contract_id: str, data: EnterpriseStatusUpdate, db: Session = Depends(get_db)) -> EmployeeContract:
    contract = db.scalar(select(EmployeeContract).where(EmployeeContract.id == contract_id, EmployeeContract.organization_id == current_identity().organization_id))
    if contract is None: raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if data.status != "TERMINATED" or contract.status != "ACTIVE": raise HTTPException(status_code=409, detail="Terminacion no permitida")
    contract.status = "TERMINATED"; contract.erp_sync_status = "PENDING"
    enqueue_erp_job(db, aggregate_type="EMPLOYEE_CONTRACT", aggregate_id=contract.id, operation="UPSERT_EMPLOYEE", idempotency_key=f"employee:{contract.id}:terminated", payload={})
    _event(db, "HR", "CONTRACT_TERMINATED", contract.employee_code)
    db.commit(); db.refresh(contract)
    return contract


@router.post("/hr/attendance", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def create_attendance(data: AttendanceCreate, db: Session = Depends(get_db)) -> AttendanceEntry:
    if db.scalar(select(EmployeeContract.id).where(EmployeeContract.id == data.contract_id, EmployeeContract.organization_id == current_identity().organization_id)) is None: raise HTTPException(status_code=404, detail="Contrato no encontrado")
    entry = AttendanceEntry(**data.model_dump(), organization_id=current_identity().organization_id, overtime_status="PENDING" if data.overtime_hours > 0 else "NOT_REQUIRED", recorded_by=audit_actor())
    db.add(entry); _event(db, "HR", "ATTENDANCE_RECORDED", data.contract_id, {"date": data.work_date.isoformat()})
    _commit(db, "Ya existe asistencia para ese empleado y fecha")
    db.refresh(entry)
    return entry


@router.patch("/hr/attendance/{attendance_id}/overtime", response_model=AttendanceRead)
def decide_overtime(attendance_id: str, data: OvertimeDecision, db: Session = Depends(get_db)) -> AttendanceEntry:
    entry = db.scalar(select(AttendanceEntry).where(AttendanceEntry.id == attendance_id, AttendanceEntry.organization_id == current_identity().organization_id))
    if entry is None: raise HTTPException(status_code=404, detail="Asistencia no encontrada")
    if entry.overtime_hours <= 0 or entry.overtime_status != "PENDING": raise HTTPException(status_code=409, detail="Estas horas extra no requieren o ya recibieron decision")
    entry.overtime_status = data.status; entry.overtime_approved_by = audit_actor(); entry.overtime_approval_note = data.note
    _event(db, "HR", f"OVERTIME_{data.status}", entry.id, {"hours": str(entry.overtime_hours)})
    db.commit(); db.refresh(entry)
    return entry


@router.post("/hr/leave-requests", response_model=LeaveRequestRead, status_code=status.HTTP_201_CREATED)
def create_leave(data: LeaveRequestCreate, db: Session = Depends(get_db)) -> LeaveRequest:
    if db.scalar(select(EmployeeContract.id).where(EmployeeContract.id == data.contract_id, EmployeeContract.organization_id == current_identity().organization_id)) is None: raise HTTPException(status_code=404, detail="Contrato no encontrado")
    item = LeaveRequest(**data.model_dump(), organization_id=current_identity().organization_id, requested_by=audit_actor())
    db.add(item); _event(db, "HR", "LEAVE_REQUESTED", item.id)
    db.commit(); db.refresh(item)
    return item


@router.patch("/hr/leave-requests/{request_id}/status", response_model=LeaveRequestRead)
def update_leave(request_id: str, data: EnterpriseStatusUpdate, db: Session = Depends(get_db)) -> LeaveRequest:
    item = db.scalar(select(LeaveRequest).where(LeaveRequest.id == request_id, LeaveRequest.organization_id == current_identity().organization_id))
    if item is None: raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if item.status != "PENDING" or data.status not in {"APPROVED", "REJECTED"}: raise HTTPException(status_code=409, detail="Decision de permiso no permitida")
    item.status = data.status; item.approved_by = audit_actor()
    _event(db, "HR", f"LEAVE_{data.status}", item.id); db.commit(); db.refresh(item)
    return item


@router.post("/hr/payroll-runs", response_model=PayrollRunRead, status_code=status.HTTP_201_CREATED)
def create_payroll(data: PayrollRunCreate, db: Session = Depends(get_db)) -> PayrollRun:
    org = current_identity().organization_id
    contracts = list(db.scalars(select(EmployeeContract).where(EmployeeContract.id.in_(data.contract_ids), EmployeeContract.organization_id == org, EmployeeContract.status == "ACTIVE")))
    if len(contracts) != len(set(data.contract_ids)): raise HTTPException(status_code=422, detail="Uno o mas contratos no existen o no estan activos")
    policies = _active_payroll_policies(db, org, data.period_end)
    policy_rules = [rule for policy in policies for rule in policy.rules_json]
    policy_reference = ",".join(policy.code for policy in policies) or None
    lines: list[dict[str, object]] = []; gross = Decimal("0")
    for contract in contracts:
        overtime = Decimal(str(db.scalar(select(func.coalesce(func.sum(AttendanceEntry.overtime_hours), 0)).where(AttendanceEntry.contract_id == contract.id, AttendanceEntry.organization_id == org, AttendanceEntry.overtime_status == "APPROVED", AttendanceEntry.work_date.between(data.period_start, data.period_end))) or 0))
        regular_hours = Decimal(str(db.scalar(select(func.coalesce(func.sum(AttendanceEntry.regular_hours), 0)).where(AttendanceEntry.contract_id == contract.id, AttendanceEntry.organization_id == org, AttendanceEntry.work_date.between(data.period_start, data.period_end))) or 0))
        worked_days = int(db.scalar(select(func.count(AttendanceEntry.id)).where(AttendanceEntry.contract_id == contract.id, AttendanceEntry.organization_id == org, AttendanceEntry.status == "PRESENT", AttendanceEntry.work_date.between(data.period_start, data.period_end))) or 0)
        hourly = contract.monthly_salary / (contract.standard_hours_weekly * Decimal("4.3333"))
        overtime_multiplier = Decimal("1.5")
        for rule in policy_rules:
            if rule.get("code") == "OVERTIME_MULTIPLIER" and rule.get("enabled", True): overtime_multiplier = Decimal(str(rule.get("rate", "1.5")))
        overtime_amount = overtime * hourly * overtime_multiplier
        employee_adjustments = [row for row in data.adjustments if row.contract_id == contract.id]
        earnings = sum((row.amount for row in employee_adjustments if row.kind in {"COMMISSION", "BONUS", "ALLOWANCE"}), Decimal("0"))
        manual_deductions = sum((row.amount for row in employee_adjustments if row.kind == "DEDUCTION"), Decimal("0"))
        period_base = _period_base(contract, data.period_start, data.period_end, regular_hours, worked_days)
        line_gross = period_base + overtime_amount + earnings
        statutory_lines = [{**rule, "amount": str(_rule_amount(rule, line_gross))} for rule in policy_rules if rule.get("side") == "EMPLOYEE_DEDUCTION" and rule.get("code") != "OVERTIME_MULTIPLIER"]
        employer_lines = [{**rule, "amount": str(_rule_amount(rule, line_gross))} for rule in policy_rules if rule.get("side") == "EMPLOYER_CONTRIBUTION"]
        statutory_deductions = sum((Decimal(row["amount"]) for row in statutory_lines), Decimal("0"))
        employer_contributions = sum((Decimal(row["amount"]) for row in employer_lines), Decimal("0"))
        deductions = manual_deductions + statutory_deductions
        line_net = line_gross - deductions
        lines.append({"contract_id": contract.id, "employee_code": contract.employee_code, "employee_name": contract.employee_name,
            "payment_type": contract.payment_type, "base_rate": str(contract.base_pay_amount), "period_base": str(period_base),
            "regular_hours": str(regular_hours), "worked_days": worked_days, "overtime_hours": str(overtime),
            "overtime_multiplier": str(overtime_multiplier), "overtime_amount": str(overtime_amount.quantize(Decimal('0.01'))),
            "adjustments": [row.model_dump(mode="json") for row in employee_adjustments], "statutory_deductions": statutory_lines,
            "employer_contributions": employer_lines, "employer_contribution_total": str(employer_contributions),
            "payroll_policy": policy_reference, "gross": str(line_gross.quantize(Decimal('0.01'))),
            "deductions": str(deductions.quantize(Decimal('0.01'))), "net": str(line_net.quantize(Decimal('0.01')))})
        gross += line_gross
    run = PayrollRun(organization_id=org, number=_number("NOM"), period_start=data.period_start, period_end=data.period_end, lines_json=lines,
        gross_total=gross.quantize(Decimal("0.01")), deduction_total=sum((Decimal(str(row["deductions"])) for row in lines), Decimal("0")).quantize(Decimal("0.01")), net_total=sum((Decimal(str(row["net"])) for row in lines), Decimal("0")).quantize(Decimal("0.01")), created_by=audit_actor())
    db.add(run); db.flush()
    for index, line in enumerate(lines, start=1):
        db.add(PayrollVoucher(organization_id=org, number=f"{run.number}-{index:04d}", payroll_run_id=run.id,
            contract_id=str(line["contract_id"]), period_start=data.period_start, period_end=data.period_end,
            gross=Decimal(str(line["gross"])), deductions=Decimal(str(line["deductions"])),
            employer_contributions=Decimal(str(line["employer_contribution_total"])), net=Decimal(str(line["net"])), details_json=line))
    _event(db, "HR", "PAYROLL_DRAFT_CREATED", run.number, {"employees": len(lines), "policy": policy_reference or "NO_POLICY"})
    db.commit(); db.refresh(run)
    return run


@router.patch("/hr/payroll-runs/{run_id}/status", response_model=PayrollRunRead)
def update_payroll(run_id: str, data: EnterpriseStatusUpdate, db: Session = Depends(get_db)) -> PayrollRun:
    run = db.scalar(select(PayrollRun).where(PayrollRun.id == run_id, PayrollRun.organization_id == current_identity().organization_id).with_for_update())
    if run is None: raise HTTPException(status_code=404, detail="Nomina no encontrada")
    transitions = {"DRAFT": {"REVIEWED", "CANCELLED"}, "REVIEWED": {"APPROVED", "DRAFT"}, "APPROVED": {"POSTED"}}
    if data.status not in transitions.get(run.status, set()): raise HTTPException(status_code=409, detail="Transicion de nomina no permitida")
    actor = audit_actor()
    if data.status == "REVIEWED":
        if actor == run.created_by:
            raise HTTPException(status_code=403, detail="La persona que preparó la nómina no puede revisarla")
        run.reviewed_by = actor
    elif data.status == "APPROVED":
        if not run.reviewed_by or actor in {run.created_by, run.reviewed_by}:
            raise HTTPException(status_code=403, detail="La aprobación requiere una tercera persona autorizada")
        run.approved_by = actor
    elif data.status == "POSTED":
        if not run.approved_by or actor in {run.created_by, run.reviewed_by, run.approved_by}:
            raise HTTPException(status_code=403, detail="La contabilización requiere separación de funciones")
        run.posted_by = actor
    elif data.status == "DRAFT":
        run.reviewed_by = None
        run.approved_by = None
        run.posted_by = None
    run.status = data.status
    vouchers = list(db.scalars(select(PayrollVoucher).where(PayrollVoucher.payroll_run_id == run.id, PayrollVoucher.organization_id == current_identity().organization_id)))
    for voucher in vouchers:
        voucher.status = data.status
        if data.status in {"APPROVED", "POSTED"} and voucher.issued_at is None: voucher.issued_at = datetime.now(UTC)
    if data.status == "APPROVED":
        run.erp_sync_status = "PENDING"
        enqueue_erp_job(db, aggregate_type="PAYROLL_RUN", aggregate_id=run.id, operation="SUBMIT_PAYROLL", idempotency_key=f"payroll:{run.id}:approved", payload={})
    _event(db, "HR", f"PAYROLL_{data.status}", run.number); db.commit(); db.refresh(run)
    return run


@router.post("/used-vehicles", response_model=UsedVehicleRead, status_code=status.HTTP_201_CREATED)
def create_used_vehicle(data: UsedVehicleCreate, db: Session = Depends(get_db)) -> UsedVehicle:
    item = UsedVehicle(**data.model_dump(exclude={"inspection", "media", "branch_id", "vin"}), organization_id=current_identity().organization_id, inspection_json=data.inspection, media_json=data.media,
        branch_id=operational_branch_id(db, data.branch_id), vin=data.vin.upper(), created_by=audit_actor())
    db.add(item); db.flush(); _event(db, "USED_VEHICLES", "APPRAISAL_CREATED", item.vin)
    _commit(db, "El VIN ya existe en inventario de usados"); db.refresh(item)
    return item


@router.patch("/used-vehicles/{vehicle_id}/status", response_model=UsedVehicleRead)
def update_used_vehicle(vehicle_id: str, data: EnterpriseStatusUpdate, db: Session = Depends(get_db)) -> UsedVehicle:
    item = db.scalar(select(UsedVehicle).where(UsedVehicle.id == vehicle_id, UsedVehicle.organization_id == current_identity().organization_id))
    if item is None: raise HTTPException(status_code=404, detail="Vehiculo usado no encontrado")
    transitions = {"APPRAISAL": {"ACQUIRED", "REJECTED"}, "ACQUIRED": {"RECONDITIONING"}, "RECONDITIONING": {"READY"}, "READY": {"PUBLISHED"}, "PUBLISHED": {"RESERVED", "SOLD"}, "RESERVED": {"PUBLISHED", "SOLD"}}
    if data.status not in transitions.get(item.status, set()): raise HTTPException(status_code=409, detail="Transicion de vehiculo no permitida")
    item.status = data.status
    if data.status == "ACQUIRED": enqueue_erp_job(db, aggregate_type="USED_VEHICLE", aggregate_id=item.id, operation="UPSERT_USED_VEHICLE_ITEM", idempotency_key=f"used:{item.id}:acquired", payload={})
    if data.status == "PUBLISHED": item.published_at = datetime.now(UTC)
    if data.status == "SOLD": item.sold_at = datetime.now(UTC)
    _event(db, "USED_VEHICLES", f"VEHICLE_{data.status}", item.vin); db.commit(); db.refresh(item)
    return item


@router.post("/social/channels", response_model=SocialChannelRead, status_code=status.HTTP_201_CREATED)
def create_social_channel(data: SocialChannelCreate, db: Session = Depends(get_db)) -> SocialChannel:
    channel = SocialChannel(**data.model_dump(), organization_id=current_identity().organization_id)
    db.add(channel); _event(db, "SOCIAL", "CHANNEL_REGISTERED", data.external_account_id)
    _commit(db, "La cuenta social ya esta registrada"); db.refresh(channel)
    return channel


@router.post("/social/conversations", response_model=SocialConversationRead, status_code=status.HTTP_201_CREATED)
def create_social_conversation(data: SocialConversationCreate, db: Session = Depends(get_db)) -> SocialConversation:
    if db.scalar(select(SocialChannel.id).where(SocialChannel.id == data.channel_id, SocialChannel.organization_id == current_identity().organization_id)) is None: raise HTTPException(status_code=404, detail="Canal no encontrado")
    conversation = SocialConversation(**data.model_dump(), organization_id=current_identity().organization_id)
    db.add(conversation); db.flush(); _event(db, "SOCIAL", "CONVERSATION_CREATED", conversation.id, {"consent": data.consent_status})
    db.commit(); db.refresh(conversation)
    return conversation


@router.post("/social/conversations/{conversation_id}/messages", response_model=SocialMessageRead, status_code=status.HTTP_201_CREATED)
def create_social_message(conversation_id: str, data: SocialMessageCreate, db: Session = Depends(get_db)) -> SocialMessage:
    conversation = db.scalar(select(SocialConversation).where(SocialConversation.id == conversation_id, SocialConversation.organization_id == current_identity().organization_id))
    if conversation is None: raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    if data.direction == "OUTBOUND" and conversation.consent_status != "OPTED_IN": raise HTTPException(status_code=409, detail="El contacto no ha autorizado mensajes salientes")
    if data.direction == "OUTBOUND" and not data.human_approved: raise HTTPException(status_code=422, detail="Una persona debe aprobar la respuesta saliente")
    channel = db.scalar(select(SocialChannel).where(SocialChannel.id == conversation.channel_id, SocialChannel.organization_id == current_identity().organization_id))
    outbound_status = "QUEUED" if channel and channel.channel_type in {"WHATSAPP", "EMAIL"} else "CONNECTOR_PENDING"
    message = SocialMessage(conversation_id=conversation_id, organization_id=current_identity().organization_id, direction=data.direction, body=data.body,
        human_approved=data.human_approved, status=outbound_status if data.direction == "OUTBOUND" else "RECEIVED", sent_by=audit_actor())
    conversation.last_message_at = datetime.now(UTC); conversation.status = "OPEN"
    db.add(message); db.flush()
    if data.direction == "OUTBOUND" and channel and channel.channel_type in {"WHATSAPP", "EMAIL"}:
        enqueue_notification(
            db,
            channel=channel.channel_type,
            recipient=conversation.contact_handle,
            subject=conversation.subject or "Respuesta SmartDiag504",
            body_text=data.body,
            template_key="SOCIAL_HUMAN_REPLY",
            aggregate_type="SOCIAL_MESSAGE",
            aggregate_id=message.id,
            idempotency_key=f"social-message:{message.id}",
            payload={"conversation_id": conversation.id, "channel_id": channel.id},
        )
    _event(db, "SOCIAL", f"MESSAGE_{message.status}", conversation_id)
    db.commit(); db.refresh(message)
    return message
    OvertimeDecision,
