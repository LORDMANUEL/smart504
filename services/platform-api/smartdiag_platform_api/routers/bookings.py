from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from ..dependencies import get_repository
from ..models import BookingRequest
from ..repositories import InMemoryRepository

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.post("")
def create_booking(
    payload: BookingRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    repository: InMemoryRepository = Depends(get_repository),
) -> JSONResponse:
    if not idempotency_key.strip():
        raise HTTPException(status_code=400, detail="Idempotency-Key is required")
    response, created = repository.create_booking(idempotency_key.strip(), payload)
    return JSONResponse(status_code=201 if created else 200, content=response.model_dump(mode="json"))
