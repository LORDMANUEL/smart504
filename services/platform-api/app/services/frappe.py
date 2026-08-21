from __future__ import annotations

import json
from collections import defaultdict
from decimal import Decimal
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import CatalogCategory, CatalogProduct
from app.text import slugify


class FrappeReadClient:
    def __init__(self, settings: Settings):
        if (
            not settings.frappe_base_url
            or not settings.frappe_api_key
            or not settings.frappe_api_secret
        ):
            raise HTTPException(
                status_code=503, detail="ERPNext integration account is not configured"
            )
        self.base_url = settings.frappe_base_url.rstrip("/")
        self.headers = {
            "Authorization": (
                f"token {settings.frappe_api_key.get_secret_value()}:"
                f"{settings.frappe_api_secret.get_secret_value()}"
            ),
            "Accept": "application/json",
        }

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=15.0, headers=self.headers) as client:
                response = client.get(f"{self.base_url}{path}", params=params)
                if response.status_code == 404:
                    return {"data": None}
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="ERPNext read request failed") from exc

    def get_resource(self, doctype: str, name: str) -> dict[str, Any]:
        return self._get(f"/api/resource/{doctype}/{name}").get("data") or {}

    def list_resource(
        self,
        doctype: str,
        *,
        fields: list[str],
        filters: list[list[Any]] | None = None,
        page_length: int = 500,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            params: dict[str, Any] = {
                "limit_start": offset,
                "limit_page_length": page_length,
            }
            # Frappe expects JSON strings for fields and filters.
            import json

            params["fields"] = json.dumps(fields)
            if filters:
                params["filters"] = json.dumps(filters)
            data = self._get(f"/api/resource/{doctype}", params=params).get("data") or []
            rows.extend(data)
            if len(data) < page_length:
                break
            offset += page_length
        return rows

    def verify_submitted_sales_invoice(self, invoice_reference: str) -> dict[str, Any]:
        invoice = self.get_resource("Sales Invoice", invoice_reference)
        if not invoice or invoice.get("name") != invoice_reference:
            raise HTTPException(status_code=409, detail="ERPNext invoice does not exist")
        if int(invoice.get("docstatus") or 0) != 1:
            raise HTTPException(status_code=409, detail="ERPNext invoice is not submitted")
        return invoice

    def get_service_order_by_external_reference(
        self, external_reference: str
    ) -> dict[str, Any] | None:
        rows = self.list_resource(
            "Service Order",
            fields=[
                "name", "title", "preference_note", "sd_external_reference",
                "sd_workflow_state", "sd_platform_diagnosis",
                "sd_platform_assigned_technicians", "sd_platform_bay_code",
                "sd_platform_parts_json", "sd_platform_labor_json",
                "sd_platform_evidence_json", "modified",
            ],
            filters=[["Service Order", "sd_external_reference", "=", external_reference]],
            page_length=1,
        )
        return rows[0] if rows else None


class FrappeWriteClient(FrappeReadClient):
    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=60.0, headers=self.headers) as client:
                response = client.post(f"{self.base_url}{path}", json=payload)
                response.raise_for_status()
                return response.json().get("message") or {}
        except httpx.HTTPStatusError as exc:
            # Keep the actionable ERP validation message, without copying the
            # complete server traceback or request credentials into our outbox.
            detail = "ERPNext rechazo el documento"
            try:
                error_payload = exc.response.json()
                raw = error_payload.get("message")
                server_messages = error_payload.get("_server_messages")
                if not raw and server_messages:
                    decoded = json.loads(server_messages) if isinstance(server_messages, str) else server_messages
                    if decoded:
                        last = json.loads(decoded[-1]) if isinstance(decoded[-1], str) else decoded[-1]
                        raw = last.get("message") if isinstance(last, dict) else last
                raw = raw or error_payload.get("exc_type") or detail
                if isinstance(raw, dict):
                    raw = raw.get("message") or raw.get("name") or detail
                detail = str(raw).splitlines()[-1][:420]
            except (ValueError, AttributeError):
                pass
            raise HTTPException(status_code=502, detail=detail) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="ERPNext write request failed") from exc

    def import_workshop_catalog(self, catalog: dict[str, Any]) -> dict[str, Any]:
        return self._post(
            "/api/method/smartdiag_workshop.api.catalog.import_workshop_catalog",
            {"catalog": catalog},
        )

    def apply_integration_command(
        self, *, operation: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return self._post(
            "/api/method/smartdiag_workshop.api.operations.apply_integration_command",
            {"command": {"operation": operation, "payload": payload}},
        )

    def _create_resource(self, doctype: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=60.0, headers=self.headers) as client:
                response = client.post(
                    f"{self.base_url}/api/resource/{quote(doctype, safe='')}", json=payload
                )
                response.raise_for_status()
                return response.json().get("data") or {}
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=502, detail=f"ERPNext could not create {doctype}"
            ) from exc

    def _update_resource(
        self, doctype: str, name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            encoded_doctype = quote(doctype, safe="")
            encoded_name = quote(name, safe="")
            with httpx.Client(timeout=60.0, headers=self.headers) as client:
                response = client.put(
                    f"{self.base_url}/api/resource/{encoded_doctype}/{encoded_name}",
                    json=payload,
                )
                response.raise_for_status()
                return response.json().get("data") or {}
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=502, detail=f"ERPNext could not update {doctype}"
            ) from exc

    def upsert_item_price(
        self, *, item_code: str, price_list: str, rate: Decimal, currency: str
    ) -> str:
        existing = self._find_one(
            "Item Price",
            fields=["name", "item_code", "price_list", "price_list_rate"],
            filters=[
                ["Item Price", "item_code", "=", item_code],
                ["Item Price", "price_list", "=", price_list],
            ],
        )
        payload = {
            "item_code": item_code,
            "price_list": price_list,
            "price_list_rate": float(rate),
            "currency": currency,
            "selling": 1,
        }
        if existing:
            self._update_resource("Item Price", str(existing["name"]), payload)
            return str(existing["name"])
        created = self._create_resource("Item Price", payload)
        return str(created["name"])

    def _submit_resource(self, doctype: str, name: str) -> dict[str, Any]:
        try:
            encoded_doctype = quote(doctype, safe="")
            encoded_name = quote(name, safe="")
            with httpx.Client(timeout=60.0, headers=self.headers) as client:
                response = client.post(
                    f"{self.base_url}/api/v2/document/{encoded_doctype}/{encoded_name}/method/submit"
                )
                response.raise_for_status()
                payload = response.json()
                return payload.get("data") or payload.get("message") or {}
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=502, detail=f"ERPNext could not submit {doctype}"
            ) from exc

    def _find_one(
        self, doctype: str, *, fields: list[str], filters: list[list[Any]]
    ) -> dict[str, Any] | None:
        rows = self.list_resource(doctype, fields=fields, filters=filters, page_length=1)
        return rows[0] if rows else None

    def _ensure_item(self, item: dict[str, Any]) -> str:
        item_code = str(item["item_code"])
        existing = self._find_one(
            "Item", fields=["name", "item_code"], filters=[["Item", "item_code", "=", item_code]]
        )
        if existing:
            return str(existing["name"])
        created = self._create_resource(
            "Item",
            {
                "item_code": item_code,
                "item_name": item.get("item_name") or item_code,
                "item_group": "Products",
                "stock_uom": "Nos",
                "is_stock_item": 1,
            },
        )
        return str(created["name"])

    def _ensure_customer(self, customer_name: str) -> str:
        existing = self._find_one(
            "Customer",
            fields=["name", "customer_name"],
            filters=[["Customer", "customer_name", "=", customer_name]],
        )
        if existing:
            return str(existing["name"])
        created = self._create_resource(
            "Customer",
            {
                "customer_name": customer_name,
                "customer_type": "Individual",
                "customer_group": "Individual",
                "territory": "All Territories",
            },
        )
        return str(created["name"])

    def _ensure_warehouse(self, warehouse_code: str, company: str, suffix: str) -> str:
        existing = self._find_one(
            "Warehouse",
            fields=["name", "warehouse_name", "company"],
            filters=[
                ["Warehouse", "warehouse_name", "=", warehouse_code],
                ["Warehouse", "company", "=", company],
            ],
        )
        if existing:
            return str(existing["name"])
        created = self._create_resource(
            "Warehouse",
            {
                "warehouse_name": warehouse_code,
                "company": company,
                "parent_warehouse": f"All Warehouses - {suffix}",
                "is_group": 0,
            },
        )
        return str(created["name"])

    def _sync_payment(
        self,
        *,
        invoice_id: str,
        operation_reference: str,
        payment_method: str,
        payment_reference: str | None,
        posting_date: str,
    ) -> str:
        existing = self._find_one(
            "Payment Entry",
            fields=["name", "docstatus", "reference_no"],
            filters=[["Payment Entry", "reference_no", "=", operation_reference]],
        )
        if existing:
            if int(existing.get("docstatus") or 0) == 0:
                self._submit_resource("Payment Entry", str(existing["name"]))
            return str(existing["name"])
        payment = self._post(
            "/api/method/erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
            {"dt": "Sales Invoice", "dn": invoice_id},
        )
        mode = {"CASH": "Cash", "CARD": "Credit Card", "TRANSFER": "Wire Transfer"}.get(
            payment_method, "Cash"
        )
        payment.update(
            {
                "mode_of_payment": mode,
                "reference_no": operation_reference,
                "reference_date": posting_date,
                "remarks": (
                    f"SmartDiag504 {operation_reference}; referencia externa "
                    f"{payment_reference or 'N/A'}"
                ),
            }
        )
        created = self._create_resource("Payment Entry", payment)
        self._submit_resource("Payment Entry", str(created["name"]))
        return str(created["name"])

    def sync_retail_sale(
        self,
        *,
        invoice_document: dict[str, Any],
        warehouse_code: str,
        company: str,
        warehouse_suffix: str,
        customer_name: str,
        payment_method: str,
        payment_reference: str | None,
    ) -> dict[str, str]:
        customer = self._ensure_customer(customer_name)
        warehouse = self._ensure_warehouse(warehouse_code, company, warehouse_suffix)
        for item in invoice_document["items"]:
            self._ensure_item(item)
            item["warehouse"] = warehouse
        invoice_document["customer"] = customer
        invoice_document["set_warehouse"] = warehouse
        operation_reference = str(invoice_document["po_no"])
        existing = self._find_one(
            "Sales Invoice",
            fields=["name", "docstatus", "po_no"],
            filters=[["Sales Invoice", "po_no", "=", operation_reference]],
        )
        if existing:
            invoice_id = str(existing["name"])
            if int(existing.get("docstatus") or 0) == 0:
                self._submit_resource("Sales Invoice", invoice_id)
        else:
            created = self._create_resource("Sales Invoice", invoice_document)
            invoice_id = str(created["name"])
            self._submit_resource("Sales Invoice", invoice_id)
        payment_id = self._sync_payment(
            invoice_id=invoice_id,
            operation_reference=operation_reference,
            payment_method=payment_method,
            payment_reference=payment_reference,
            posting_date=str(invoice_document["posting_date"]),
        )
        return {"invoice_id": invoice_id, "payment_id": payment_id}


def verify_invoice_reference(*, invoice_reference: str, settings: Settings) -> dict[str, Any]:
    if settings.invoice_verification_mode.lower() in {"development", "test"}:
        return {"name": invoice_reference, "docstatus": 1, "verification": "development"}
    return FrappeReadClient(settings).verify_submitted_sales_invoice(invoice_reference)


def projected_catalog_price(
    erp_rate: Decimal, current_rate: Decimal | None
) -> Decimal:
    """Do not erase a usable storefront price when ERP lacks a selling rate."""
    if erp_rate > 0:
        return erp_rate
    return current_rate or Decimal("0")


def sync_catalog_projection(db: Session, settings: Settings) -> dict[str, int]:
    client = FrappeReadClient(settings)
    items = client.list_resource(
        "Item",
        fields=[
            "item_code",
            "item_name",
            "item_group",
            "brand",
            "description",
            "disabled",
            "is_stock_item",
            "image",
        ],
        filters=[["Item", "disabled", "=", 0]],
    )
    prices = client.list_resource(
        "Item Price",
        fields=["item_code", "price_list", "price_list_rate", "currency"],
        filters=[["Item Price", "price_list", "=", settings.frappe_price_list]],
    )
    bins = client.list_resource(
        "Bin", fields=["item_code", "actual_qty", "valuation_rate", "warehouse"]
    )

    price_map = {row["item_code"]: row for row in prices if row.get("item_code")}
    stock_map: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    cost_map: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in bins:
        item_code = row.get("item_code")
        if item_code:
            stock_map[item_code] += Decimal(str(row.get("actual_qty") or 0))
            cost_map[item_code] = max(
                cost_map[item_code], Decimal(str(row.get("valuation_rate") or 0))
            )

    category_map: dict[str, CatalogCategory] = {
        category.name: category for category in db.scalars(select(CatalogCategory))
    }
    created = 0
    updated = 0
    for row in items:
        item_code = str(row.get("item_code") or "").strip()
        if not item_code:
            continue
        group_name = str(row.get("item_group") or "Sin categoría").strip()
        category = category_map.get(group_name)
        if category is None:
            category = CatalogCategory(
                name=group_name,
                slug=slugify(group_name),
                description=f"Artículos sincronizados desde ERPNext: {group_name}",
                active=True,
            )
            db.add(category)
            db.flush()
            category_map[group_name] = category

        product = db.scalar(select(CatalogProduct).where(CatalogProduct.sku == item_code))
        price = price_map.get(item_code, {})
        erp_rate = Decimal(str(price.get("price_list_rate") or 0))
        values = {
            "name": row.get("item_name") or item_code,
            "slug": slugify(f"{row.get('item_name') or item_code}-{item_code}"),
            "short_description": (row.get("description") or "")[:320] or None,
            "description": row.get("description"),
            "category_id": category.id,
            "brand": row.get("brand"),
            "price": projected_catalog_price(erp_rate, product.price if product else None),
            "purchase_cost": cost_map[item_code],
            "currency": price.get("currency") or "HNL",
            "stock_qty": stock_map[item_code],
            "stock_status": "IN_STOCK" if stock_map[item_code] > 0 else "OUT_OF_STOCK",
            "active": True,
            "source_system": "ERPNEXT",
            "source_reference": item_code,
        }
        if product is None:
            product = CatalogProduct(
                sku=item_code, compatibility_notes="Validar aplicación por VIN.", **values
            )
            db.add(product)
            created += 1
        else:
            for key, value in values.items():
                setattr(product, key, value)
            product.version += 1
            updated += 1
    db.commit()
    return {"items_read": len(items), "created": created, "updated": updated}
