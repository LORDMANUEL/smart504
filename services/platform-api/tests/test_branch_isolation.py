from sqlalchemy import select
import pytest
from fastapi import HTTPException

from app.db import SessionLocal
from app.models import Branch, CashSession
from app.request_context import begin_request, end_request, set_staff_identity
from app.services.branch_scope import operational_branch_id
from app.routes.operations_control import _ensure_default_structure


def test_operational_transactions_are_isolated_by_assigned_branch() -> None:
    reset_token = begin_request()
    try:
        set_staff_identity(
            actor="system-test",
            organization_id="SMARTDIAG504",
            branch_id=None,
            is_recovery=True,
        )
        with SessionLocal() as db:
            branch_a = Branch(code="BR-SEC-A", name="Sucursal seguridad A", active=True)
            branch_b = Branch(code="BR-SEC-B", name="Sucursal seguridad B", active=True)
            db.add_all([branch_a, branch_b])
            db.flush()
            db.add_all(
                [
                    CashSession(branch_id=branch_a.id, opened_by="A", opening_balance=0, status="CLOSED"),
                    CashSession(branch_id=branch_b.id, opened_by="B", opening_balance=0, status="CLOSED"),
                ]
            )
            db.commit()
            branch_a_id, branch_b_id = branch_a.id, branch_b.id

        with SessionLocal() as db:
            main_branch_id = db.scalar(select(Branch.id).where(Branch.code == "MAIN"))
            assert operational_branch_id(db) == main_branch_id

        set_staff_identity(
            actor="cashier-a",
            organization_id="SMARTDIAG504",
            branch_id=branch_a_id,
            enforce_branch_scope=True,
        )
        with SessionLocal() as db:
            with pytest.raises(HTTPException) as cross_branch:
                operational_branch_id(db, branch_b_id)
            assert getattr(cross_branch.value, "status_code", None) == 403
            visible_branches = list(db.scalars(select(Branch)))
            assert [item.id for item in visible_branches] == [branch_a_id]
            visible = list(db.scalars(select(CashSession)))
            assert visible
            assert {item.branch_id for item in visible} == {branch_a_id}
            db.add(CashSession(branch_id=branch_b_id, opened_by="intruder", opening_balance=0))
            with pytest.raises(ValueError, match="Cross-branch"):
                db.commit()
    finally:
        end_request(reset_token)


def test_branch_scoped_overview_bootstrap_does_not_duplicate_main_branch() -> None:
    """Regression: a scoped technician must not recreate hidden org defaults."""
    reset_token = begin_request()
    try:
        set_staff_identity(
            actor="system-test",
            organization_id="SMARTDIAG504",
            branch_id=None,
            is_recovery=True,
        )
        with SessionLocal() as db:
            scoped_branch = Branch(code="BR-UX-TECH", name="Sucursal técnico UX", active=True)
            db.add(scoped_branch)
            db.commit()
            scoped_branch_id = scoped_branch.id

        set_staff_identity(
            actor="technician-ux",
            organization_id="SMARTDIAG504",
            branch_id=scoped_branch_id,
            enforce_branch_scope=True,
        )
        with SessionLocal() as db:
            _ensure_default_structure(db)
            all_main = list(
                db.scalars(
                    select(Branch)
                    .where(Branch.organization_id == "SMARTDIAG504", Branch.code == "MAIN")
                    .execution_options(include_all_tenants=True)
                )
            )
            assert len(all_main) == 1
    finally:
        end_request(reset_token)
