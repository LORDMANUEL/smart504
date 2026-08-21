from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import require_admin
from app.config import get_settings
from app.db import get_db
from app.models import CatalogCategory, CatalogProduct, CatalogProductImage
from app.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    GoogleImageResult,
    ImageImportRequest,
    ImageReorderRequest,
    ProductCreate,
    ProductImageRead,
    ProductRead,
    ProductUpdate,
)
from app.services.frappe import sync_catalog_projection
from app.services.google_images import search_google_images
from app.services.media import delete_stored_image, import_remote_image, store_upload
from app.services.catalog_cache import invalidate_public_catalog_cache
from app.text import slugify

router = APIRouter(
    prefix="/api/v1/admin/catalog",
    tags=["admin-catalog"],
    dependencies=[Depends(require_admin)],
)


def _category_or_404(db: Session, category_id: str) -> CatalogCategory:
    category = db.get(CatalogCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def _product_or_404(db: Session, product_id: str) -> CatalogProduct:
    product = db.scalar(
        select(CatalogProduct)
        .where(CatalogProduct.id == product_id)
        .options(selectinload(CatalogProduct.images))
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc
    invalidate_public_catalog_cache()


@router.get("/categories", response_model=list[CategoryRead])
def admin_list_categories(db: Session = Depends(get_db)) -> list[CatalogCategory]:
    return list(db.scalars(select(CatalogCategory).order_by(CatalogCategory.sort_order)))


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)) -> CatalogCategory:
    category = CatalogCategory(
        **data.model_dump(exclude={"slug"}),
        slug=slugify(data.slug or data.name),
    )
    db.add(category)
    _commit_or_conflict(db, "A category with that name or slug already exists")
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: str,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CatalogCategory:
    category = _category_or_404(db, category_id)
    changes = data.model_dump(exclude_unset=True)
    if "slug" in changes and changes["slug"]:
        changes["slug"] = slugify(changes["slug"])
    for field, value in changes.items():
        setattr(category, field, value)
    _commit_or_conflict(db, "Category update conflicts with an existing record")
    db.refresh(category)
    return category


@router.get("/products", response_model=list[ProductRead])
def admin_list_products(db: Session = Depends(get_db)) -> list[CatalogProduct]:
    return list(
        db.scalars(
            select(CatalogProduct)
            .options(selectinload(CatalogProduct.images))
            .order_by(CatalogProduct.name)
        ).unique()
    )


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db)) -> CatalogProduct:
    if data.category_id:
        _category_or_404(db, data.category_id)
    product = CatalogProduct(
        **data.model_dump(exclude={"slug", "sku"}),
        slug=slugify(data.slug or data.name),
        sku=data.sku.strip().upper(),
    )
    db.add(product)
    _commit_or_conflict(db, "A product with that SKU or slug already exists")
    return _product_or_404(db, product.id)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_admin_product(product_id: str, db: Session = Depends(get_db)) -> CatalogProduct:
    return _product_or_404(db, product_id)


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: str,
    data: ProductUpdate,
    db: Session = Depends(get_db),
) -> CatalogProduct:
    product = _product_or_404(db, product_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("category_id"):
        _category_or_404(db, changes["category_id"])
    if changes.get("slug"):
        changes["slug"] = slugify(changes["slug"])
    for field, value in changes.items():
        setattr(product, field, value)
    product.version += 1
    _commit_or_conflict(db, "Product update conflicts with an existing record")
    return _product_or_404(db, product_id)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_product(product_id: str, db: Session = Depends(get_db)) -> Response:
    product = _product_or_404(db, product_id)
    product.active = False
    product.version += 1
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _set_primary(db: Session, product_id: str, primary_image_id: str) -> None:
    images = list(
        db.scalars(select(CatalogProductImage).where(CatalogProductImage.product_id == product_id))
    )
    for image in images:
        image.is_primary = image.id == primary_image_id


@router.post(
    "/products/{product_id}/images/upload",
    response_model=ProductImageRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: str,
    image: UploadFile = File(...),
    alt_text: str = Form(..., min_length=2, max_length=240),
    attribution_text: str | None = Form(default=None),
    license_name: str | None = Form(default=None),
    license_url: str | None = Form(default=None),
    make_primary: bool = Form(default=False),
    db: Session = Depends(get_db),
) -> CatalogProductImage:
    product = _product_or_404(db, product_id)
    settings = get_settings()
    stored = await store_upload(upload=image, product_id=product_id, settings=settings)
    record = CatalogProductImage(
        product_id=product_id,
        storage_path=stored.storage_path,
        public_url=stored.public_url,
        alt_text=alt_text.strip(),
        source_type="UPLOAD",
        attribution_text=attribution_text,
        license_name=license_name,
        license_url=license_url,
        mime_type=stored.mime_type,
        sha256=stored.sha256,
        width=stored.width,
        height=stored.height,
        is_primary=make_primary or not product.images,
        sort_order=len(product.images),
    )
    db.add(record)
    _commit_or_conflict(db, "This exact image is already attached to the product")
    if record.is_primary:
        _set_primary(db, product_id, record.id)
        db.commit()
    db.refresh(record)
    return record


@router.post(
    "/products/{product_id}/images/import",
    response_model=ProductImageRead,
    status_code=status.HTTP_201_CREATED,
)
async def import_product_image(
    product_id: str,
    data: ImageImportRequest,
    db: Session = Depends(get_db),
) -> CatalogProductImage:
    product = _product_or_404(db, product_id)
    settings = get_settings()
    stored = await import_remote_image(
        url=str(data.image_url), product_id=product_id, settings=settings
    )
    record = CatalogProductImage(
        product_id=product_id,
        storage_path=stored.storage_path,
        public_url=stored.public_url,
        alt_text=data.alt_text.strip(),
        source_type="GOOGLE" if data.source_page_url else "EXTERNAL",
        source_url=str(data.image_url),
        source_page_url=str(data.source_page_url) if data.source_page_url else None,
        attribution_text=data.attribution_text,
        license_name=data.license_name,
        license_url=str(data.license_url) if data.license_url else None,
        mime_type=stored.mime_type,
        sha256=stored.sha256,
        width=stored.width,
        height=stored.height,
        is_primary=data.make_primary or not product.images,
        sort_order=len(product.images),
    )
    db.add(record)
    _commit_or_conflict(db, "This exact image is already attached to the product")
    if record.is_primary:
        _set_primary(db, product_id, record.id)
        db.commit()
    db.refresh(record)
    return record


@router.post("/products/{product_id}/images/reorder", response_model=list[ProductImageRead])
def reorder_images(
    product_id: str,
    data: ImageReorderRequest,
    db: Session = Depends(get_db),
) -> list[CatalogProductImage]:
    _product_or_404(db, product_id)
    images = list(
        db.scalars(select(CatalogProductImage).where(CatalogProductImage.product_id == product_id))
    )
    image_map = {image.id: image for image in images}
    if set(data.image_ids) != set(image_map):
        raise HTTPException(
            status_code=422, detail="The image order must include every product image"
        )
    for index, image_id in enumerate(data.image_ids):
        image_map[image_id].sort_order = index
    if data.primary_image_id:
        if data.primary_image_id not in image_map:
            raise HTTPException(status_code=422, detail="Primary image is not attached to product")
        _set_primary(db, product_id, data.primary_image_id)
    db.commit()
    return list(
        db.scalars(
            select(CatalogProductImage)
            .where(CatalogProductImage.product_id == product_id)
            .order_by(CatalogProductImage.sort_order)
        )
    )


@router.delete("/products/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(product_id: str, image_id: str, db: Session = Depends(get_db)) -> Response:
    image = db.scalar(
        select(CatalogProductImage).where(
            CatalogProductImage.id == image_id,
            CatalogProductImage.product_id == product_id,
        )
    )
    if not image:
        raise HTTPException(status_code=404, detail="Product image not found")
    was_primary = image.is_primary
    storage_path = image.storage_path
    db.delete(image)
    db.flush()
    if was_primary:
        replacement = db.scalar(
            select(CatalogProductImage)
            .where(CatalogProductImage.product_id == product_id)
            .order_by(CatalogProductImage.sort_order)
        )
        if replacement:
            replacement.is_primary = True
    db.commit()
    delete_stored_image(storage_path=storage_path, settings=get_settings())
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/images/google", response_model=list[GoogleImageResult])
async def google_image_search(
    q: str = Query(min_length=3, max_length=120),
    count: int = Query(default=8, ge=1, le=10),
) -> list[GoogleImageResult]:
    return await search_google_images(query=q, count=count, settings=get_settings())


@router.post("/sync/erpnext")
def sync_from_erpnext(db: Session = Depends(get_db)) -> dict[str, int]:
    return sync_catalog_projection(db, get_settings())
