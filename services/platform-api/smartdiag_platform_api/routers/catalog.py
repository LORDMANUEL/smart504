from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_repository
from ..models import ProductPage
from ..repositories import InMemoryRepository

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


@router.get("/products", response_model=ProductPage)
def list_products(
    q: str | None = Query(default=None, max_length=100),
    make: str | None = Query(default=None, max_length=60),
    model: str | None = Query(default=None, max_length=60),
    year: int | None = Query(default=None, ge=1900, le=2100),
    repository: InMemoryRepository = Depends(get_repository),
) -> ProductPage:
    items = repository.list_products(query=q, make=make, model=model, year=year)
    return ProductPage(items=items, total=len(items))
