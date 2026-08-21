from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from html import escape

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_authenticated_staff
from app.db import get_db
from app.models import AttendanceEntry, EmployeeContract, FlowEvent, LeaveRequest, PayrollVoucher, StaffUser
from app.request_context import audit_actor, current_identity
from app.schemas import AttendanceRead, EmployeeContractRead, LeaveRequestRead, PayrollVoucherRead


router = APIRouter(
    prefix="/api/v1/staff/self-service",
    tags=["employee-self-service"],
    dependencies=[Depends(require_authenticated_staff)],
)
HONDURAS_TZ = timezone(timedelta(hours=-6))


class SelfServiceOverview(BaseModel):
    linked: bool
    contract: EmployeeContractRead | None
    today_attendance: AttendanceRead | None
    leave_requests: list[LeaveRequestRead]
    vouchers: list[PayrollVoucherRead]


class PunchRequest(BaseModel):
    action: str = Field(pattern=r"^(CHECK_IN|CHECK_OUT)$")
    note: str | None = Field(default=None, max_length=500)


class OwnLeaveRequest(BaseModel):
    leave_type: str = Field(pattern=r"^(VACATION|SICK|PERSONAL|MATERNITY|PATERNITY|UNPAID)$")
    start_date: str
    end_date: str
    reason: str | None = Field(default=None, max_length=500)


def _find_contract(db: Session) -> EmployeeContract | None:
    identity = current_identity()
    staff_user_id = db.scalar(select(StaffUser.id).where(StaffUser.organization_id == identity.organization_id, StaffUser.employee_code == identity.actor))
    contract = None
    if staff_user_id is not None:
        contract = db.scalar(select(EmployeeContract).where(EmployeeContract.organization_id == identity.organization_id,
            EmployeeContract.staff_user_id == staff_user_id, EmployeeContract.status == "ACTIVE"))
    if contract is None:
        contract = db.scalar(select(EmployeeContract).where(EmployeeContract.organization_id == identity.organization_id,
            EmployeeContract.employee_code == identity.actor, EmployeeContract.status == "ACTIVE"))
    return contract


def _contract(db: Session) -> EmployeeContract:
    contract = _find_contract(db)
    if contract is None:
        raise HTTPException(status_code=404, detail="Su usuario aún no está vinculado a un contrato activo. RR. HH. debe vincularlo.")
    return contract


@router.get("/overview", response_model=SelfServiceOverview)
def overview(db: Session = Depends(get_db)) -> SelfServiceOverview:
    contract = _find_contract(db)
    if contract is None:
        return SelfServiceOverview(linked=False, contract=None, today_attendance=None, leave_requests=[], vouchers=[])
    local_date = datetime.now(HONDURAS_TZ).date()
    attendance = db.scalar(select(AttendanceEntry).where(AttendanceEntry.contract_id == contract.id, AttendanceEntry.work_date == local_date))
    leaves = list(db.scalars(select(LeaveRequest).where(LeaveRequest.contract_id == contract.id).order_by(LeaveRequest.created_at.desc()).limit(50)))
    vouchers = list(db.scalars(select(PayrollVoucher).where(PayrollVoucher.contract_id == contract.id, PayrollVoucher.status.in_(["APPROVED", "POSTED"])).order_by(PayrollVoucher.period_end.desc()).limit(50)))
    return SelfServiceOverview(linked=True, contract=contract, today_attendance=attendance, leave_requests=leaves, vouchers=vouchers)


@router.post("/punch", response_model=AttendanceRead)
def punch(data: PunchRequest, db: Session = Depends(get_db)) -> AttendanceEntry:
    contract = _contract(db)
    now = datetime.now(UTC)
    work_date = datetime.now(HONDURAS_TZ).date()
    entry = db.scalar(select(AttendanceEntry).where(AttendanceEntry.contract_id == contract.id, AttendanceEntry.work_date == work_date))
    if data.action == "CHECK_IN":
        if entry and entry.check_in_at:
            raise HTTPException(status_code=409, detail="La entrada de hoy ya fue marcada")
        if entry is None:
            entry = AttendanceEntry(organization_id=current_identity().organization_id, contract_id=contract.id, work_date=work_date,
                regular_hours=Decimal("0"), overtime_hours=Decimal("0"), status="PRESENT", check_in_at=now,
                note=data.note, recorded_by=audit_actor())
            db.add(entry)
        else:
            entry.check_in_at = now; entry.note = data.note or entry.note
        action = "EMPLOYEE_CHECKED_IN"
    else:
        if entry is None or entry.check_in_at is None:
            raise HTTPException(status_code=409, detail="Primero debe marcar la entrada")
        if entry.check_out_at:
            raise HTTPException(status_code=409, detail="La salida de hoy ya fue marcada")
        entry.check_out_at = now; entry.note = data.note or entry.note
        started = entry.check_in_at if entry.check_in_at.tzinfo else entry.check_in_at.replace(tzinfo=UTC)
        total_hours = max(Decimal("0"), Decimal(str((now - started).total_seconds() / 3600))).quantize(Decimal("0.01"))
        scheduled = min(total_hours, Decimal("8"))
        entry.regular_hours = scheduled
        entry.overtime_hours = max(Decimal("0"), total_hours - scheduled)
        entry.overtime_status = "PENDING" if entry.overtime_hours > 0 else "NOT_REQUIRED"
        action = "EMPLOYEE_CHECKED_OUT"
    db.add(FlowEvent(organization_id=current_identity().organization_id, module="HR", action=action,
        item_reference=contract.employee_code, actor=audit_actor(), result="SUCCESS", metadata_json={"work_date": work_date.isoformat()}))
    db.commit(); db.refresh(entry)
    return entry


@router.post("/leave-requests", response_model=LeaveRequestRead)
def request_leave(data: OwnLeaveRequest, db: Session = Depends(get_db)) -> LeaveRequest:
    from datetime import date
    contract = _contract(db)
    try:
        start_date, end_date = date.fromisoformat(data.start_date), date.fromisoformat(data.end_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Las fechas deben usar formato AAAA-MM-DD") from exc
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="La fecha final no puede ser anterior al inicio")
    item = LeaveRequest(organization_id=current_identity().organization_id, contract_id=contract.id, leave_type=data.leave_type,
        start_date=start_date, end_date=end_date, reason=data.reason, requested_by=audit_actor())
    db.add_all([item, FlowEvent(organization_id=current_identity().organization_id, module="HR", action="SELF_SERVICE_LEAVE_REQUESTED",
        item_reference=contract.employee_code, actor=audit_actor(), result="SUCCESS", metadata_json={"leave_type": data.leave_type})])
    db.commit(); db.refresh(item)
    return item


@router.get("/vouchers/{voucher_id}/html", response_class=HTMLResponse)
def own_voucher_html(voucher_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    """Renderiza un comprobante aislado; nunca permite leer el voucher de otro empleado."""
    contract = _contract(db)
    voucher = db.scalar(select(PayrollVoucher).where(
        PayrollVoucher.id == voucher_id,
        PayrollVoucher.organization_id == current_identity().organization_id,
        PayrollVoucher.contract_id == contract.id,
        PayrollVoucher.status.in_(["APPROVED", "POSTED"]),
    ))
    if voucher is None:
        raise HTTPException(status_code=404, detail="Voucher no encontrado")
    money = lambda value: f"L {Decimal(value):,.2f}"
    safe_name = escape(contract.employee_name)
    safe_code = escape(contract.employee_code)
    safe_number = escape(voucher.number)
    content = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Voucher {safe_number}</title><style>
@page {{ size: Letter portrait; margin: 12mm; }}
body {{ font: 14px Arial, sans-serif; color:#111827; max-width:760px; margin:auto; }}
header {{ border-bottom:3px solid #ef101b; padding-bottom:12px; margin-bottom:20px; }}
h1 {{ margin:0; }} small {{ color:#667085; }} table {{ width:100%; border-collapse:collapse; }}
th,td {{ padding:10px; border-bottom:1px solid #d8dee8; text-align:left; }}
td:last-child,th:last-child {{ text-align:right; }} .net {{ font-size:20px; font-weight:800; }}
.actions {{ margin:24px 0; }} @media print {{ .actions {{ display:none; }} }}
</style></head><body><header><small>SmartDiag504 · comprobante de pago</small><h1>{safe_number}</h1>
<p>{safe_name} · {safe_code}<br>Período {voucher.period_start.isoformat()} al {voucher.period_end.isoformat()}</p></header>
<table><thead><tr><th>Concepto</th><th>Valor</th></tr></thead><tbody>
<tr><td>Ingreso bruto</td><td>{money(voucher.gross)}</td></tr>
<tr><td>Deducciones</td><td>- {money(voucher.deductions)}</td></tr>
<tr><td>Aportes patronales informativos</td><td>{money(voucher.employer_contributions)}</td></tr>
<tr class="net"><td>Neto a pagar</td><td>{money(voucher.net)}</td></tr></tbody></table>
<p><small>Documento generado desde una versión aprobada de nómina. Verifique con RR. HH. cualquier diferencia.</small></p>
<div class="actions"><button onclick="window.print()">Imprimir o guardar PDF</button></div></body></html>"""
    return HTMLResponse(content, headers={"Cache-Control": "private, no-store"})
