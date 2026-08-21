from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.config import Settings
from app.models import (
    CatalogProduct,
    Customer,
    ErpIntegrationJob,
    EmployeeContract,
    ImportCase,
    InventoryBalance,
    InventoryTransfer,
    PayrollRun,
    PurchaseOrder,
    Quote,
    Supplier,
    UsedVehicle,
    Vehicle,
    WarehouseLocation,
    WorkOrder,
    WorkOrderLaborEntry,
)
from app.request_context import worker_identity
from app.services.frappe import FrappeWriteClient


RETRYABLE_STATUSES = ("PENDING", "FAILED")


def _work_order_payload(
    work_order: WorkOrder,
    settings: Settings,
    labor_entries: list[WorkOrderLaborEntry] | None = None,
) -> dict[str, Any]:
    vehicle = work_order.vehicle
    customer = work_order.customer
    if not vehicle.vin or not vehicle.model_year:
        raise ValueError("La OT necesita VIN y ano-modelo antes de sincronizar con ERPNext")
    return {
        "work_order_number": work_order.number,
        "company": settings.frappe_company,
        "selling_price_list": settings.frappe_price_list,
        "customer_id": customer.id,
        "customer_name": customer.full_name,
        "customer_phone": customer.phone,
        "customer_tax_id": customer.tax_id,
        "vin": vehicle.vin,
        "plate": vehicle.plate,
        "make": vehicle.make,
        "model": vehicle.model,
        "model_year": vehicle.model_year,
        "engine": vehicle.engine,
        "mileage_km": vehicle.mileage_km,
        "title": work_order.title,
        "concern": work_order.concern,
        "status": work_order.status,
        "promised_at": work_order.promised_at.isoformat() if work_order.promised_at else None,
        "due_date": work_order.promised_at.date().isoformat() if work_order.promised_at else None,
        "diagnosis": work_order.diagnosis,
        "assigned_technicians": work_order.assigned_technicians,
        "bay_code": work_order.bay_code,
        "parts_required": work_order.parts_required or [],
        "labor_entries": [
            {
                "id": row.id, "service_code": row.service_code,
                "description": row.description, "technician": row.technician_name,
                "rate_kind": row.rate_kind, "hours": float(row.hours),
                "sale_total": float(row.sale_total),
            }
            for row in (labor_entries or [])
        ],
        "evidence": [
            {
                "id": event.payload.get("id"), "category": event.payload.get("category"),
                "caption": event.payload.get("caption"), "actor": event.actor,
                "created_at": event.payload.get("created_at"),
            }
            for event in work_order.events
            if event.event_type == "DIAGNOSTIC_EVIDENCE_ADDED"
        ],
        "platform_updated_at": work_order.updated_at.isoformat() if work_order.updated_at else None,
    }


def _command_payload(db: Session, job: ErpIntegrationJob, settings: Settings) -> dict[str, Any]:
    if job.aggregate_type == "WORK_ORDER":
        work_order = db.scalar(
            select(WorkOrder)
            .where(WorkOrder.id == job.aggregate_id)
            .options(joinedload(WorkOrder.customer), joinedload(WorkOrder.vehicle))
        )
        if work_order is None:
            raise ValueError("La proyeccion local de la OT ya no existe")
        if job.operation == "UPSERT_SERVICE_ORDER":
            labor_entries = list(db.scalars(select(WorkOrderLaborEntry).where(
                WorkOrderLaborEntry.work_order_id == work_order.id
            ).order_by(WorkOrderLaborEntry.created_at)))
            return _work_order_payload(work_order, settings, labor_entries)
    if job.aggregate_type == "QUOTE" and job.operation == "UPSERT_SERVICE_QUOTATION":
        quote = db.scalar(
            select(Quote).where(Quote.id == job.aggregate_id).options(selectinload(Quote.lines))
        )
        if quote is None or not quote.customer_id or not quote.vehicle_id:
            raise ValueError("La cotizacion no tiene cliente y vehiculo validos")
        linked_order = db.get(WorkOrder, quote.work_order_id) if quote.work_order_id else None
        customer = linked_order.customer if linked_order else db.get(Customer, quote.customer_id)
        vehicle = db.get(Vehicle, quote.vehicle_id)
        if customer is None or vehicle is None:
            raise ValueError("La cotizacion no tiene cliente y vehiculo validos")
        return {
            "quote_number": quote.number,
            "company": settings.frappe_company,
            "selling_price_list": settings.frappe_price_list,
            "customer_id": customer.id,
            "customer_name": customer.full_name,
            "customer_phone": customer.phone,
            "customer_tax_id": customer.tax_id,
            "vin": vehicle.vin,
            "plate": vehicle.plate,
            "make": vehicle.make,
            "model": vehicle.model,
            "model_year": vehicle.model_year,
            "engine": vehicle.engine,
            "mileage_km": vehicle.mileage_km,
            "status": quote.status,
            "notes": quote.notes,
            "discount": float(quote.discount),
            "tax": float(quote.tax),
            "items": [
                {
                    "item_code": line.code,
                    "item_name": line.description,
                    "description": line.description,
                    "qty": float(line.quantity),
                    "rate": float(line.unit_price),
                    "is_stock_item": line.line_type == "PART",
                    "approval_status": line.approval_status,
                }
                for line in quote.lines
                if line.approval_status != "REJECTED"
            ],
        }
    if job.aggregate_type == "INVENTORY_TRANSFER" and job.operation == "SUBMIT_STOCK_TRANSFER":
        transfer = db.get(InventoryTransfer, job.aggregate_id)
        if transfer is None:
            raise ValueError("El traslado local ya no existe")
        source = db.get(WarehouseLocation, transfer.from_warehouse_id)
        target = db.get(WarehouseLocation, transfer.to_warehouse_id)
        if source is None or target is None:
            raise ValueError("El traslado no tiene bodegas validas")
        items: list[dict[str, object]] = []
        for row in transfer.items_json:
            product = None
            if row.get("product_id"):
                product = db.get(CatalogProduct, str(row["product_id"]))
            code = str(row.get("sku") or (product.sku if product else "")).strip()
            quantity = float(row.get("quantity") or row.get("qty") or 0)
            if not code or quantity <= 0:
                raise ValueError("Cada linea del traslado requiere producto/SKU y cantidad positiva")
            items.append({"item_code": code, "item_name": product.name if product else code, "qty": quantity})
        return {
            "transfer_number": transfer.number,
            "company": settings.frappe_company,
            "from_warehouse": source.code,
            "to_warehouse": target.code,
            "items": items,
        }
    if job.aggregate_type == "SUPPLIER" and job.operation == "UPSERT_SUPPLIER":
        supplier = db.get(Supplier, job.aggregate_id)
        if supplier is None:
            raise ValueError("El proveedor ya no existe")
        return {"supplier_code": supplier.code, "supplier_name": supplier.name, "tax_id": supplier.tax_id,
                "email": supplier.email, "phone": supplier.phone, "currency": supplier.currency}
    if job.aggregate_type == "PURCHASE_ORDER" and job.operation == "UPSERT_PURCHASE_ORDER":
        order = db.get(PurchaseOrder, job.aggregate_id)
        if order is None:
            raise ValueError("La orden de compra ya no existe")
        supplier = db.get(Supplier, order.supplier_id)
        if supplier is None:
            raise ValueError("La orden de compra no tiene proveedor")
        return {"purchase_order_number": order.number, "company": settings.frappe_company,
                "supplier_code": supplier.code, "supplier_name": supplier.name, "tax_id": supplier.tax_id,
                "status": order.status, "currency": order.currency, "exchange_rate": float(order.exchange_rate),
                "expected_at": order.expected_at.isoformat() if order.expected_at else None,
                "items": order.items_json, **dict(job.payload_json)}
    if job.aggregate_type == "IMPORT_CASE" and job.operation == "SUBMIT_LANDED_COST":
        case = db.get(ImportCase, job.aggregate_id)
        order = db.get(PurchaseOrder, case.purchase_order_id) if case else None
        if case is None or order is None or not order.erpnext_purchase_order_id:
            raise ValueError("La importacion requiere una orden de compra sincronizada")
        return {"import_number": case.number, "company": settings.frappe_company,
                "purchase_order": order.erpnext_purchase_order_id, "allocation_method": case.allocation_method,
                "costs": case.costs_json}
    if job.aggregate_type == "EMPLOYEE_CONTRACT" and job.operation == "UPSERT_EMPLOYEE":
        contract = db.get(EmployeeContract, job.aggregate_id)
        if contract is None:
            raise ValueError("El contrato ya no existe")
        return {"employee_code": contract.employee_code, "employee_name": contract.employee_name,
                "date_of_birth": contract.date_of_birth.isoformat() if contract.date_of_birth else None,
                "national_id": contract.national_id, "address": contract.address, "phone": contract.phone,
                "email": contract.email, "social_security_number": contract.social_security_number,
                "insurance_provider": contract.insurance_provider, "insurance_member_number": contract.insurance_member_number,
                "job_title": contract.job_title, "contract_type": contract.contract_type,
                "start_date": contract.start_date.isoformat(), "end_date": contract.end_date.isoformat() if contract.end_date else None,
                "monthly_salary": float(contract.monthly_salary), "currency": contract.currency,
                "company": settings.frappe_company, "status": contract.status}
    if job.aggregate_type == "PAYROLL_RUN" and job.operation == "SUBMIT_PAYROLL":
        run = db.get(PayrollRun, job.aggregate_id)
        if run is None:
            raise ValueError("La nomina ya no existe")
        return {"payroll_number": run.number, "company": settings.frappe_company,
                "period_start": run.period_start.isoformat(), "period_end": run.period_end.isoformat(),
                "payroll_frequency": {"MONTHLY": "Monthly", "BIWEEKLY": "Fortnightly", "WEEKLY": "Weekly", "DAILY": "Daily", "HOURLY": "Monthly"}.get(str(run.lines_json[0].get("payment_type")) if run.lines_json else "MONTHLY", "Monthly"),
                "lines": run.lines_json, "gross_total": float(run.gross_total), "net_total": float(run.net_total)}
    if job.aggregate_type == "USED_VEHICLE" and job.operation == "UPSERT_USED_VEHICLE_ITEM":
        vehicle = db.get(UsedVehicle, job.aggregate_id)
        if vehicle is None:
            raise ValueError("El vehiculo usado ya no existe")
        return {"vin": vehicle.vin, "make": vehicle.make, "model": vehicle.model, "model_year": vehicle.model_year,
                "mileage_km": vehicle.mileage_km, "acquisition_type": vehicle.acquisition_type,
                "acquisition_cost": float(vehicle.acquisition_cost), "target_sale_price": float(vehicle.target_sale_price),
                "company": settings.frappe_company}
    return dict(job.payload_json)


def process_erp_jobs(
    db: Session,
    settings: Settings,
    *,
    limit: int = 25,
    client: FrappeWriteClient | None = None,
    job_ids: set[str] | None = None,
) -> dict[str, int]:
    """Deliver pending commands; never marks a command synced without ERP evidence."""
    now = datetime.now(UTC)
    query = (
        select(ErpIntegrationJob)
        .where(
            ErpIntegrationJob.status.in_(RETRYABLE_STATUSES),
            (ErpIntegrationJob.next_attempt_at.is_(None))
            | (ErpIntegrationJob.next_attempt_at <= now),
        )
        .order_by(ErpIntegrationJob.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
        .execution_options(include_all_tenants=True)
    )
    if job_ids:
        query = query.where(ErpIntegrationJob.id.in_(job_ids))
    jobs = list(
        db.scalars(
            query
        )
    )
    counters = {"selected": len(jobs), "synced": 0, "failed": 0, "blocked": 0}
    if not jobs:
        return counters
    if client is None:
        try:
            client = FrappeWriteClient(settings)
        except HTTPException as exc:
            for job in jobs:
                with worker_identity(actor="erp-sync-worker", organization_id=job.organization_id):
                    job.status = "BLOCKED"
                    job.last_error = str(exc.detail)[:500]
                    job.attempts += 1
                    work_order = db.get(WorkOrder, job.aggregate_id)
                    if work_order:
                        work_order.erp_sync_status = "BLOCKED"
                        work_order.erp_sync_error = job.last_error
                    quote = db.get(Quote, job.aggregate_id)
                    if quote:
                        quote.erp_sync_status = "BLOCKED"
                        quote.erp_sync_error = job.last_error
                    transfer = db.get(InventoryTransfer, job.aggregate_id)
                    if transfer:
                        transfer.erp_sync_status = "BLOCKED"
                        transfer.erp_sync_error = job.last_error
                    db.commit()
            counters["blocked"] = len(jobs)
            return counters

    for job in jobs:
        tenant_context = worker_identity(actor="erp-sync-worker", organization_id=job.organization_id)
        tenant_context.__enter__()
        job.attempts += 1
        work_order = db.get(WorkOrder, job.aggregate_id) if job.aggregate_type == "WORK_ORDER" else None
        quote = db.get(Quote, job.aggregate_id) if job.aggregate_type == "QUOTE" else None
        transfer = db.get(InventoryTransfer, job.aggregate_id) if job.aggregate_type == "INVENTORY_TRANSFER" else None
        supplier = db.get(Supplier, job.aggregate_id) if job.aggregate_type == "SUPPLIER" else None
        purchase_order = db.get(PurchaseOrder, job.aggregate_id) if job.aggregate_type == "PURCHASE_ORDER" else None
        import_case = db.get(ImportCase, job.aggregate_id) if job.aggregate_type == "IMPORT_CASE" else None
        employee_contract = db.get(EmployeeContract, job.aggregate_id) if job.aggregate_type == "EMPLOYEE_CONTRACT" else None
        payroll_run = db.get(PayrollRun, job.aggregate_id) if job.aggregate_type == "PAYROLL_RUN" else None
        used_vehicle = db.get(UsedVehicle, job.aggregate_id) if job.aggregate_type == "USED_VEHICLE" else None
        try:
            payload = _command_payload(db, job, settings)
            result = client.apply_integration_command(
                operation=job.operation, payload=payload
            )
            target = str(result.get("name") or "").strip()
            if not target:
                raise ValueError("ERPNext no devolvio la referencia del documento")
            job.status = "SYNCED"
            job.target_reference = target
            job.last_error = None
            job.processed_at = now
            job.next_attempt_at = None
            if work_order:
                work_order.erpnext_service_order_id = target
                work_order.erp_sync_status = "SYNCED"
                work_order.erp_sync_error = None
                work_order.erp_last_synced_at = now
            if quote:
                quote.erpnext_quotation_id = target
                quote.erp_sync_status = "SYNCED"
                quote.erp_sync_error = None
                quote.erp_last_synced_at = now
            if transfer:
                # PostgreSQL is an operational projection. Reflect quantities
                # only after ERPNext accepts the Stock Entry, and only once.
                if transfer.status != "RECEIVED":
                    for row in transfer.items_json:
                        product = None
                        if row.get("product_id"):
                            product = db.get(CatalogProduct, str(row["product_id"]))
                        if product is None and row.get("sku"):
                            product = db.scalar(
                                select(CatalogProduct).where(
                                    CatalogProduct.sku == str(row["sku"])
                                )
                            )
                        if product is None:
                            raise ValueError("El repuesto confirmado por ERP no existe en la proyeccion")
                        quantity = Decimal(str(row.get("quantity") or row.get("qty") or 0))
                        source_balance = db.scalar(
                            select(InventoryBalance)
                            .where(
                                InventoryBalance.warehouse_id == transfer.from_warehouse_id,
                                InventoryBalance.product_id == product.id,
                            )
                            .with_for_update()
                        )
                        if source_balance is None or source_balance.quantity_on_hand < quantity:
                            raise ValueError("La proyeccion local no puede conciliar el traslado confirmado")
                        target_balance = db.scalar(
                            select(InventoryBalance)
                            .where(
                                InventoryBalance.warehouse_id == transfer.to_warehouse_id,
                                InventoryBalance.product_id == product.id,
                            )
                            .with_for_update()
                        )
                        if target_balance is None:
                            target_balance = InventoryBalance(
                                organization_id=transfer.organization_id,
                                warehouse_id=transfer.to_warehouse_id,
                                product_id=product.id,
                                quantity_on_hand=Decimal("0"),
                                quantity_reserved=Decimal("0"),
                                source_reference=target,
                            )
                            db.add(target_balance)
                        source_balance.quantity_on_hand -= quantity
                        target_balance.quantity_on_hand += quantity
                        target_balance.source_reference = target
                transfer.erpnext_stock_entry_id = target
                transfer.erp_sync_status = "SYNCED"
                transfer.erp_sync_error = None
                transfer.erp_last_synced_at = now
                transfer.status = "RECEIVED"
            if supplier:
                supplier.erpnext_supplier_id = target; supplier.erp_sync_status = "SYNCED"; supplier.erp_sync_error = None
            if purchase_order:
                purchase_order.erpnext_purchase_order_id = target; purchase_order.erp_sync_status = "SYNCED"; purchase_order.erp_sync_error = None; purchase_order.erp_last_synced_at = now
            if import_case:
                import_case.erpnext_landed_cost_id = target; import_case.landed_cost_status = "SYNCED"
            if employee_contract:
                employee_contract.erpnext_employee_id = target; employee_contract.erp_sync_status = "SYNCED"
            if payroll_run:
                # ERPNext/HRMS creates the authoritative payroll draft.  SmartDiag must
                # not claim that accounting was posted until HRMS submits that document.
                payroll_run.erpnext_payroll_entry_id = target
                payroll_run.erp_sync_status = "SYNCED"
            if used_vehicle:
                used_vehicle.erpnext_item_id = target
            counters["synced"] += 1
        except Exception as exc:  # boundary converts provider errors into durable state
            message = str(getattr(exc, "detail", exc))[:500]
            job.status = "FAILED"
            job.last_error = message
            job.next_attempt_at = now + timedelta(minutes=min(60, 2 ** min(job.attempts, 5)))
            if work_order:
                work_order.erp_sync_status = "FAILED"
                work_order.erp_sync_error = message
            if quote:
                quote.erp_sync_status = "FAILED"
                quote.erp_sync_error = message
            if transfer:
                transfer.erp_sync_status = "FAILED"
                transfer.erp_sync_error = message
            if supplier:
                supplier.erp_sync_status = "FAILED"; supplier.erp_sync_error = message
            if purchase_order:
                purchase_order.erp_sync_status = "FAILED"; purchase_order.erp_sync_error = message
            if import_case:
                import_case.landed_cost_status = "FAILED"
            if employee_contract:
                employee_contract.erp_sync_status = "FAILED"
            if payroll_run:
                payroll_run.erp_sync_status = "FAILED"
            counters["failed"] += 1
        db.commit()
        tenant_context.__exit__(None, None, None)
    return counters
