from __future__ import annotations

import json
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Booking, CatalogCategory, CatalogProduct, FlowEvent
from app.request_context import current_identity
from app.schemas import BookingCreate, BookingRead, CategoryRead, ProductRead
from app.services.branch_scope import operational_branch_id
from app.config import Settings, get_settings
from app.services.public_abuse import enforce_public_limit, reject_honeypot
from app.services.catalog_cache import catalog_cache_version

router = APIRouter(prefix="/api/v1", tags=["public"])
_catalog_cache_lock = Lock()


@router.get("/catalog/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)) -> list[CatalogCategory]:
    return list(
        db.scalars(
            select(CatalogCategory)
            .where(CatalogCategory.active.is_(True))
            .order_by(CatalogCategory.sort_order, CatalogCategory.name)
        )
    )


@router.get("/catalog/products", response_model=list[ProductRead])
def list_products(
    response: Response,
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=140),
    featured: bool | None = None,
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    response.headers["Cache-Control"] = "public, max-age=15, s-maxage=30, stale-while-revalidate=60"
    redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1) if settings.redis_url else None
    cache_version = catalog_cache_version(redis_client)
    cache_key = f"smartdiag:catalog:v1:{cache_version}:{q or ''}:{category or ''}:{featured}:{limit}:{offset}"
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except RedisError:
            redis_client = None
    with _catalog_cache_lock:
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except RedisError:
                redis_client = None
        statement = (
            select(CatalogProduct)
            .where(CatalogProduct.active.is_(True))
            .options(selectinload(CatalogProduct.images))
            .order_by(CatalogProduct.featured.desc(), CatalogProduct.name)
            .offset(offset)
            .limit(limit)
        )
        if q:
            pattern = f"%{q.strip()}%"
            statement = statement.where(
                or_(
                    CatalogProduct.name.ilike(pattern),
                    CatalogProduct.sku.ilike(pattern),
                    CatalogProduct.brand.ilike(pattern),
                    CatalogProduct.short_description.ilike(pattern),
                )
            )
        if category:
            statement = statement.join(CatalogCategory).where(CatalogCategory.slug == category)
        if featured is not None:
            statement = statement.where(CatalogProduct.featured.is_(featured))
        products = list(db.scalars(statement).unique())
        payload = [ProductRead.model_validate(product).model_dump(mode="json") for product in products]
        if redis_client:
            try:
                redis_client.setex(cache_key, 30, json.dumps(payload, separators=(",", ":")))
            except RedisError:
                pass
        return payload


@router.get("/catalog/products/{slug}", response_model=ProductRead)
def get_product(slug: str, db: Session = Depends(get_db)) -> CatalogProduct:
    product = db.scalar(
        select(CatalogProduct)
        .where(CatalogProduct.slug == slug, CatalogProduct.active.is_(True))
        .options(selectinload(CatalogProduct.images))
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/catalog/fitment")
def catalog_fitment(
    vin: str = Query(min_length=11, max_length=40),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    # A public VIN must never confirm whether a customer's vehicle exists in the workshop database.
    # Authenticated portal and staff flows perform the ownership/role-scoped lookup instead.
    return {
        "status": "AUTH_REQUIRED",
        "vehicle": None,
        "products": [],
        "message": "Inicie sesión para consultar compatibilidad por VIN sin exponer datos privados.",
        "login_path": "/lading/loginclie",
    }


@router.post("/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreate,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Booking:
    reject_honeypot(data.website)
    enforce_public_limit(request, settings, surface="booking", limit=settings.public_booking_limit_per_minute)
    booking = Booking(**data.model_dump(exclude={"website"}), branch_id=operational_branch_id(db))
    db.add(booking)
    try:
        db.flush()
        db.add(
            FlowEvent(
                module="RECEPTION",
                action="BOOKING_CREATED",
                item_reference=booking.id,
                actor="public-web",
                result="SUCCESS",
                metadata_json={
                    "vehicle": booking.vehicle_summary,
                    "service": booking.service_requested,
                    "preferred_date": booking.preferred_date,
                },
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Booking could not be created") from exc
    db.refresh(booking)
    return booking
