from __future__ import annotations

from datetime import UTC, datetime
from html import escape

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import FlowEvent
from app.schemas import ApprovalDecision
from app.services.approvals import load_approval_by_token


router = APIRouter(prefix="/api/v1/public/approvals", tags=["public-approvals"])


@router.get("/{token}", response_class=HTMLResponse)
def approval_page(token: str, db: Session = Depends(get_db)) -> HTMLResponse:
    approval = load_approval_by_token(db, token)
    label = "devolucion" if approval.request_type == "RETURN" else "garantia"
    disabled = approval.status != "PENDING"
    return HTMLResponse(f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Autorización SmartDiag504</title><style>
    body{{margin:0;background:#f4f6f8;font:16px Arial;color:#17181c}}main{{max-width:640px;margin:7vh auto;background:white;padding:clamp(22px,5vw,36px);border-radius:18px;box-shadow:0 20px 60px #17203318}}img{{width:150px;max-width:100%}}small{{color:#677386}}h1{{font-size:clamp(24px,6vw,30px)}}.reason{{padding:18px;background:#f6f7f9;border-left:4px solid #e51021}}button{{min-width:120px;min-height:44px;padding:14px 20px;border:0;border-radius:9px;font-weight:700;cursor:pointer}}button:focus-visible,textarea:focus-visible{{outline:3px solid #1769e0;outline-offset:3px}}.approve{{background:#14804a;color:white}}.reject{{background:#17181c;color:white}}textarea{{box-sizing:border-box;width:100%;min-height:90px;margin:14px 0;padding:12px}}.actions{{display:flex;gap:10px;flex-wrap:wrap}}</style></head><body><main><img src='/brand/smartdiag504-logo.png' alt='SmartDiag504'><small>AUTORIZACIÓN DEL PROPIETARIO</small><h1>Solicitud de {label}</h1><p>Referencia de venta: <b>{escape(str(approval.payload_json.get('sale_number', approval.sale_id)))}</b></p><div class='reason'>{escape(approval.reason)}</div><p>Estado actual: <b>{escape(approval.status)}</b></p>{'' if disabled else f'''<form method="post" action="/api/v1/public/approvals/{escape(token)}/decision-form"><label for="comment">Comentario opcional para auditoría</label><textarea id="comment" name="comment" maxlength="500"></textarea><div class="actions"><button class="approve" name="decision" value="APPROVED">Autorizar</button><button class="reject" name="decision" value="REJECTED">Rechazar</button></div></form>'''}</main></body></html>""")


def _record_decision(token: str, decision: str, comment: str | None, request: Request, db: Session) -> dict[str, str]:
    if decision not in {"APPROVED", "REJECTED"}:
        raise HTTPException(status_code=422, detail="Decisión no válida")
    approval = load_approval_by_token(db, token, for_update=True)
    if approval.status != "PENDING":
        raise HTTPException(status_code=409, detail=f"La solicitud ya está {approval.status}")
    approval.status = decision
    approval.decided_by = "public-approval-link"
    approval.decision_comment = comment
    approval.decided_at = datetime.now(UTC)
    db.add(FlowEvent(module="APPROVALS", action=f"{approval.request_type}_{decision}", item_reference=approval.id, actor="public-approval-link", result="SUCCESS", metadata_json={"sale_id": approval.sale_id, "verification": "bearer-link", "target_owner_email": approval.owner_email, "user_agent": (request.headers.get("user-agent") or "")[:180]}))
    db.commit()
    return {"id": approval.id, "status": approval.status}


@router.post("/{token}/decision")
def decide_approval(token: str, data: ApprovalDecision, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    return _record_decision(token, data.decision, data.comment, request, db)


@router.post("/{token}/decision-form", response_class=HTMLResponse)
def decide_approval_form(token: str, request: Request, decision: str = Form(...), comment: str | None = Form(default=None, max_length=500), db: Session = Depends(get_db)) -> HTMLResponse:
    result = _record_decision(token, decision, comment, request, db)
    return HTMLResponse(f"<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Decisión registrada</title></head><body><main style='max-width:640px;margin:10vh auto;font:18px Arial;padding:24px'><h1>Decisión registrada</h1><p>Estado: <strong>{escape(result['status'])}</strong></p><p>Puede cerrar esta ventana.</p></main></body></html>")
