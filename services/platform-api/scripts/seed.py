from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from smartdiag_domain.work_orders import WorkOrderStatus
from sqlalchemy import select
from fastapi_users.password import PasswordHelper

from app.config import get_settings
from app.db import SessionLocal
from app.demo_data import DEMO_PARTS, PRELOADED_PARTS, VEHICLE_CATALOG
from app.models import (
    CatalogCategory,
    CatalogProduct,
    CatalogProductImage,
    ClientUser,
    Customer,
    DocumentTemplate,
    DocumentTemplateVersion,
    Quote,
    QuoteLine,
    Vehicle,
    VehicleHistoryEvent,
    WorkOrder,
    WorkshopSetting,
)
from app.schemas import WorkOrderCreate, WorkOrderTransition, WorkOrderUpdate
from app.services.media import _store_bytes
from app.services.work_orders import create_work_order, transition, update_work_order

BASE_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = BASE_DIR / "seed_assets" / "products"


def image_metadata() -> dict[str, dict[str, object]]:
    path = ASSET_DIR / "ATTRIBUTIONS.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    if isinstance(payload, list):
        result = {}
        for item in payload:
            if isinstance(item, dict):
                filename = item.get("filename") or item.get("file") or item.get("name")
                if filename:
                    result[str(filename)] = item
        return result
    if isinstance(payload, dict):
        return {str(key): value for key, value in payload.items() if isinstance(value, dict)}
    return {}


def seed_catalog() -> None:
    settings = get_settings()
    settings.media_root.mkdir(parents=True, exist_ok=True)
    metadata = image_metadata()
    image_files = (
        sorted(
            path
            for path in ASSET_DIR.iterdir()
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        if ASSET_DIR.exists()
        else []
    )

    categories = [
        ("Filtros", "filtros", "Filtros de aceite, aire, combustible y cabina."),
        ("Frenos", "frenos", "Componentes para inspección y servicio del sistema de frenos."),
        ("Encendido", "encendido", "Bujías y componentes de encendido."),
        ("Fluidos", "fluidos", "Aceites, refrigerantes y fluidos de mantenimiento."),
    ]
    products = [
        {
            "sku": "SD-OIL-FILTER-001",
            "name": "Filtro de aceite de motor",
            "slug": "filtro-aceite-motor",
            "category": "filtros",
            "brand": "SmartSelect",
            "price": Decimal("285.00"),
            "stock_qty": Decimal("18"),
            "description": (
                "Filtro de servicio para mantenimiento preventivo. "
                "Confirme aplicación por VIN antes de instalar."
            ),
            "compatibility_notes": "Compatibilidad requiere validación por VIN, motor y año.",
        },
        {
            "sku": "SD-AIR-FILTER-001",
            "name": "Filtro de aire de motor",
            "slug": "filtro-aire-motor",
            "category": "filtros",
            "brand": "SmartSelect",
            "price": Decimal("420.00"),
            "stock_qty": Decimal("11"),
            "description": (
                "Elemento filtrante para admisión. La forma y referencia "
                "cambian según motorización."
            ),
            "compatibility_notes": "Validar por VIN o número de parte original.",
        },
        {
            "sku": "SD-BRAKE-DISC-001",
            "name": "Disco de freno delantero",
            "slug": "disco-freno-delantero",
            "category": "frenos",
            "brand": "SmartSelect",
            "price": Decimal("1850.00"),
            "stock_qty": Decimal("6"),
            "description": (
                "Disco ventilado de reemplazo. Se recomienda inspeccionar "
                "pastillas, cáliper y líquido."
            ),
            "compatibility_notes": "La medida debe confirmarse por VIN y especificación del eje.",
        },
        {
            "sku": "SD-SPARK-PLUG-001",
            "name": "Bujía de encendido",
            "slug": "bujia-encendido",
            "category": "encendido",
            "brand": "SmartSelect",
            "price": Decimal("320.00"),
            "stock_qty": Decimal("24"),
            "description": (
                "Bujía individual para servicio de encendido. Torque y "
                "calibración según fabricante."
            ),
            "compatibility_notes": "Confirmar grado térmico, rosca y calibración por motor.",
        },
    ]
    vehicle_labels = {
        vehicle["id"]: f"{vehicle['make']} {vehicle['model']} {vehicle['year']}"
        for vehicle in VEHICLE_CATALOG
    }
    products.extend(
        {
            "sku": part["code"],
            "name": part["description"],
            "slug": part["code"].lower(),
            "category": "filtros"
            if "FIL" in part["code"] or "AIR" in part["code"]
            else "frenos"
            if "BRK" in part["code"]
            else "encendido",
            "brand": "SmartSelect Demo",
            "price": Decimal(str(part["price"])),
            "stock_qty": Decimal(str(part["stock"])),
            "description": (
                f"Repuesto demo compatible con {vehicle_labels[part['vehicle_id']]}. "
                f"Ubicación de bodega {part['location']}."
            ),
            "compatibility_notes": vehicle_labels[part["vehicle_id"]],
            "active": True,
        }
        for part in DEMO_PARTS
    )
    products.extend(
        {
            "sku": part["code"],
            "name": f"{part['description']} · {vehicle_labels[part['vehicle_id']]}",
            "slug": part["code"].lower(),
            "category": "filtros" if part["code"].endswith(("-OIL", "-AIR")) else "frenos",
            "brand": "Catálogo por completar",
            "price": Decimal("0.00"),
            "stock_qty": Decimal("0"),
            "description": (
                "Ficha interna precargada. Agregue número de parte, costo, precio, "
                "existencia y fotografía después de validar por VIN."
            ),
            "compatibility_notes": (
                f"{vehicle_labels[part['vehicle_id']]} · Requiere validación por VIN, "
                "motor y versión."
            ),
            "active": False,
        }
        for part in PRELOADED_PARTS
    )

    with SessionLocal() as db:
        category_map: dict[str, CatalogCategory] = {}
        for name, slug, description in categories:
            category = db.scalar(select(CatalogCategory).where(CatalogCategory.slug == slug))
            if category is None:
                category = CatalogCategory(
                    name=name, slug=slug, description=description, active=True
                )
                db.add(category)
                db.flush()
            category_map[slug] = category

        for index, product_data in enumerate(products):
            product = db.scalar(
                select(CatalogProduct).where(CatalogProduct.sku == product_data["sku"])
            )
            if product is None:
                product = CatalogProduct(
                    sku=product_data["sku"],
                    name=product_data["name"],
                    slug=product_data["slug"],
                    short_description=product_data["description"][:300],
                    description=product_data["description"],
                    category_id=category_map[product_data["category"]].id,
                    brand=product_data["brand"],
                    price=product_data["price"],
                    currency="HNL",
                    stock_qty=product_data["stock_qty"],
                    stock_status="IN_STOCK" if product_data["stock_qty"] > 0 else "ON_REQUEST",
                    active=bool(product_data.get("active", True)),
                    featured=index < 3,
                    compatibility_notes=product_data["compatibility_notes"],
                    source_system="SEED",
                )
                db.add(product)
                db.flush()
            if image_files and not product.images:
                image_file = image_files[index % len(image_files)]
                stored = _store_bytes(
                    content=image_file.read_bytes(), product_id=product.id, settings=settings
                )
                info = metadata.get(image_file.name, {})
                record = CatalogProductImage(
                    product_id=product.id,
                    storage_path=stored.storage_path,
                    public_url=stored.public_url,
                    alt_text=f"Imagen generica de referencia para {product.name}; validar pieza por VIN",
                    source_type="AI_GENERATED",
                    source_url=str(info.get("image_url") or info.get("url") or "") or None,
                    source_page_url=str(info.get("description_url") or info.get("page_url") or "")
                    or None,
                    attribution_text=str(
                        info.get("artist") or info.get("attribution") or "Wikimedia Commons"
                    ),
                    license_name=str(
                        info.get("license") or info.get("license_short_name") or "See source"
                    ),
                    license_url=str(info.get("license_url") or "") or None,
                    mime_type=stored.mime_type,
                    sha256=stored.sha256,
                    width=stored.width,
                    height=stored.height,
                    is_primary=True,
                    sort_order=0,
                )
                db.add(record)
        setting = db.get(WorkshopSetting, "workshop_ui")
        if setting is None:
            db.add(
                WorkshopSetting(
                    key="workshop_ui",
                    value={
                        "default_view": "KANBAN",
                        "bays_enabled": False,
                        "bay_codes": ["B-01", "B-02", "B-03", "B-04"],
                    },
                )
            )
        db.commit()


def seed_work_orders() -> None:
    with SessionLocal() as db:
        customer = db.scalar(select(Customer).where(Customer.phone == "+504 9999-1001"))
        if customer is None:
            customer = Customer(
                full_name="Cliente de demostración SmartDiag",
                phone="+504 9999-1001",
                email="cliente.demo@example.com",
            )
            db.add(customer)
            db.flush()
        vehicle = db.scalar(select(Vehicle).where(Vehicle.vin == "DEMO-SMARTDIAG-0001"))
        if vehicle is None:
            vehicle = Vehicle(
                customer_id=customer.id,
                vin="DEMO-SMARTDIAG-0001",
                plate="HDEMO01",
                make="Ford",
                model="Escape",
                model_year=2020,
                engine="2.0 EcoBoost",
                transmission="Automática",
                mileage_km=86240,
                photo_url="/vehicles/ford-escape-2020.png",
            )
            db.add(vehicle)
            db.flush()
        elif not vehicle.photo_url:
            vehicle.photo_url = "/vehicles/ford-escape-2020.png"

        extra_vehicles = [
            ("1FMCU0G6XLUA12545", "HAA5040", "Ford", "Escape", 2020, "2.0 EcoBoost", 86240, "/vehicles/ford-escape-2020.png"),
            ("1FTFW1E45LFA15050", "HAB1500", "Ford", "F-150", 2020, "3.5 EcoBoost", 68450, "/vehicles/ford-f150-2020.png"),
            ("2HGFA16538H508504", "HAC2008", "Honda", "Civic", 2008, "1.8 i-VTEC", 143200, "/vehicles/honda-civic-2008.png"),
        ]
        for vin, plate, make, model, year, engine, mileage, photo_url in extra_vehicles:
            if db.scalar(select(Vehicle).where(Vehicle.vin == vin)) is None:
                db.add(Vehicle(customer_id=customer.id, vin=vin, plate=plate, make=make, model=model,
                               model_year=year, engine=engine, mileage_km=mileage, photo_url=photo_url))
        settings = get_settings()
        client_email = settings.client_demo_email.lower()
        client_user = db.scalar(
            select(ClientUser).execution_options(include_all_tenants=True).where(ClientUser.email == client_email)
        )
        if client_user is None:
            db.add(ClientUser(
                email=client_email,
                hashed_password=PasswordHelper().hash(settings.client_demo_password.get_secret_value()),
                is_active=True,
                is_verified=True,
                is_superuser=False,
                organization_id=customer.organization_id,
                customer_id=customer.id,
                username="cliente.demo",
                full_name=customer.full_name,
                loyalty_enabled=True,
                loyalty_points=245,
            ))
        db.commit()

        if db.scalar(select(VehicleHistoryEvent).where(VehicleHistoryEvent.reference == "MANT-DEMO-ACEITE-001")) is None:
            db.add_all([
                VehicleHistoryEvent(vehicle_id=vehicle.id, vin=vehicle.vin or "DEMO-SMARTDIAG-0001", event_type="MAINTENANCE",
                                    reference="MANT-DEMO-ACEITE-001", summary="Cambio de aceite sintético y filtro completado.",
                                    mileage_km=82040, quality_result="APROBADO", actor="seed@smartdiag504.local"),
                VehicleHistoryEvent(vehicle_id=vehicle.id, vin=vehicle.vin or "DEMO-SMARTDIAG-0001", event_type="DIAGNOSIS",
                                    reference="DIAG-DEMO-002", summary="Diagnóstico electrónico sin códigos críticos activos.",
                                    mileage_km=84620, quality_result="APROBADO", actor="seed@smartdiag504.local"),
            ])
            db.commit()


        statuses = list(WorkOrderStatus)
        for position, target_status in enumerate(statuses, start=1):
            number = f"OT-DEMO-{position:03d}"
            existing = db.scalar(select(WorkOrder).where(WorkOrder.number == number))
            if existing:
                continue
            work_order = create_work_order(
                db,
                WorkOrderCreate(
                    number=number,
                    customer_id=customer.id,
                    vehicle_id=vehicle.id,
                    title=[
                        "Diagnóstico electrónico inicial",
                        "Cotización de mantenimiento mayor",
                        "Aprobación de reparación de frenos",
                        "Espera de repuesto de transmisión",
                        "Servicio terminado y controlado",
                        "Servicio entregado y facturado",
                    ][position - 1],
                    concern="Vehículo ingresado para demostración integral del flujo SmartDiag504.",
                    assigned_technicians=["Técnico demo"],
                    bay_code=f"B-0{min(position, 4)}",
                    promised_at=datetime.now(UTC) + timedelta(days=position),
                    actor="seed@smartdiag504.local",
                ),
            )
            update_work_order(
                db,
                work_order.id,
                WorkOrderUpdate(
                    diagnosis="Diagnóstico técnico de demostración documentado.",
                    technician_quote={"labor": "1850.00", "parts": "2400.00", "currency": "HNL"},
                    parts_required=[{"sku": "SD-OIL-FILTER-001", "qty": 1}],
                ),
            )
            transition_sequence = [
                WorkOrderStatus.QUOTED_BY_TECHNICIAN,
                WorkOrderStatus.PENDING_CUSTOMER_APPROVAL,
                WorkOrderStatus.PENDING_PARTS,
                WorkOrderStatus.READY_TO_INVOICE,
                WorkOrderStatus.INVOICED,
            ]
            for step_index, next_status in enumerate(transition_sequence, start=1):
                if statuses.index(target_status) < step_index:
                    break
                transition(
                    db,
                    work_order.id,
                    WorkOrderTransition(
                        to_status=next_status.value,
                        actor="seed@smartdiag504.local",
                        reason=f"Avance de demostración a {next_status.value}",
                        invoice_reference="ACC-SINV-DEMO-0001"
                        if next_status == WorkOrderStatus.INVOICED
                        else None,
                        idempotency_key=f"seed:{number}:{next_status.value}",
                    ),
                )

        demo_quote = db.scalar(select(Quote).where(Quote.number == "COT-DEMO-0183"))
        ready_order = db.scalar(select(WorkOrder).where(WorkOrder.number == "OT-DEMO-005"))
        if demo_quote is None and ready_order is not None:
            demo_quote = Quote(
                organization_id=ready_order.organization_id,
                branch_id=ready_order.branch_id,
                number="COT-DEMO-0183",
                work_order_id=ready_order.id,
                status="APPROVED",
                notes="Cotización demo aprobada y disponible para probar el cobro en caja.",
                discount=Decimal("0.00"),
                tax=Decimal("0.00"),
                created_by="seed@smartdiag504.local",
                approved_by="cliente.demo@smartdiag504.com",
                approved_at=datetime.now(UTC),
            )
            demo_quote.lines = [
                QuoteLine(
                    line_type="LABOR",
                    code="MO-DIAG-001",
                    description="Diagnóstico electrónico completo",
                    quantity=Decimal("1"),
                    unit_cost=Decimal("720.00"),
                    unit_price=Decimal("1200.00"),
                ),
                QuoteLine(
                    line_type="LABOR",
                    code="MO-FRENO-001",
                    description="Servicio de frenos delanteros",
                    quantity=Decimal("1"),
                    unit_cost=Decimal("1050.00"),
                    unit_price=Decimal("1850.00"),
                ),
                QuoteLine(
                    line_type="PART",
                    code="SD-BRAKE-PAD-ESC20",
                    description="Juego de pastillas delanteras",
                    quantity=Decimal("1"),
                    unit_cost=Decimal("980.00"),
                    unit_price=Decimal("1535.00"),
                ),
            ]
            db.add(demo_quote)
            ready_order.technician_quote = {
                "quote_number": demo_quote.number,
                "status": demo_quote.status,
                "total": "4585.00",
                "currency": "HNL",
            }
            db.commit()


def seed_document_templates() -> None:
    base_css = """body{font-family:Helvetica,Arial,sans-serif;color:#17181c;font-size:10pt}header{border-bottom:3px solid #ed111c;padding-bottom:12px;margin-bottom:20px}h1{margin:0}h2{margin:5px 0;color:#ed111c}.meta{line-height:1.7;margin:18px 0}table{width:100%;border-collapse:collapse}th{padding:8px;background:#17181c;color:#fff;text-align:left}td{padding:8px;border-bottom:1px solid #ddd}.totals{display:flex;justify-content:flex-end;gap:22px;margin-top:22px;font-size:14pt}footer{margin-top:34px;color:#666;font-size:8pt}"""
    quote_body = """<header><h1>{{ company.name }}</h1><h2>{{ document.title }} {{ document.number }}</h2></header><section class="meta"><b>Cliente:</b> {{ customer.name }}<br><b>Vehiculo:</b> {{ vehicle.label }}<br><b>OT:</b> {{ work_order.number }}</section><table><thead><tr><th>Codigo</th><th>Descripcion</th><th>Cant.</th><th>Precio</th><th>Total</th><th>Aprobacion</th></tr></thead><tbody>{{ quote.rows_html }}</tbody></table><section class="totals"><span>Total</span><strong>{{ quote.total }}</strong></section><footer>{{ document.notes }}</footer>"""
    diagnosis_body = """<header><h1>{{ company.name }}</h1><h2>{{ document.title }}</h2></header><section class="meta"><b>OT:</b> {{ work_order.number }}<br><b>Cliente:</b> {{ customer.name }}<br><b>Vehiculo:</b> {{ vehicle.label }}<br><b>Estado:</b> {{ work_order.status }}</section><h2>Diagnostico</h2><p>{{ work_order.diagnosis }}</p><h2>Evidencia</h2><table><thead><tr><th>Tipo</th><th>Descripcion</th><th>Tecnico</th></tr></thead><tbody>{{ evidence.rows_html }}</tbody></table><footer>{{ document.notes }}</footer>"""
    warehouse_body = """<header><h1>{{ company.name }}</h1><h2>{{ document.title }}</h2></header><section class="meta"><b>OT:</b> {{ work_order.number }}<br><b>Vehiculo:</b> {{ vehicle.label }}</section><table><thead><tr><th>Codigo</th><th>Repuesto</th><th>Cantidad</th><th>Ubicacion</th><th>Estado</th></tr></thead><tbody>{{ warehouse.rows_html }}</tbody></table><footer>Responsable: ____________________ &nbsp; Recibe: ____________________</footer>"""
    definitions = [
        ("DEFAULT_QUOTE", "Cotizacion SmartDiag504", "QUOTE", quote_body),
        ("DEFAULT_INVOICE", "Factura SmartDiag504", "INVOICE", quote_body),
        ("DEFAULT_DIAGNOSIS", "Diagnostico con evidencia", "DIAGNOSIS", diagnosis_body),
        ("DEFAULT_PICKING", "Ticket de picking", "PICKING_TICKET", warehouse_body),
    ]
    with SessionLocal() as db:
        for code, name, document_type, body in definitions:
            if db.scalar(select(DocumentTemplate.id).where(DocumentTemplate.code == code)):
                continue
            template = DocumentTemplate(code=code, name=name, document_type=document_type,
                status="PUBLISHED", current_version=1, published_version=1)
            template.versions.append(DocumentTemplateVersion(
                version=1, status="PUBLISHED", paper_size="LETTER", html_template=body,
                css_text=base_css, variables_json=[], change_note="Plantilla inicial SmartDiag504",
                created_by="seed@smartdiag504.local", published_at=datetime.now(UTC),
            ))
            db.add(template)
        db.commit()


def main() -> int:
    settings = get_settings()
    if not settings.seed_demo_data:
        print("SmartDiag504 demo seed skipped (SEED_DEMO_DATA=false)")
        return 0
    seed_catalog()
    seed_work_orders()
    seed_document_templates()
    print("SmartDiag504 seed completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
