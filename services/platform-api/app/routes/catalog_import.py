from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.auth import require_admin
from app.config import Settings, get_settings
from app.services.catalog_import import (
    CatalogPreview,
    build_catalog_workbook,
    parse_catalog_workbook,
)
from app.services.frappe import FrappeWriteClient
from app.services.malware import scan_bytes

router = APIRouter(
    prefix="/api/v1/operations/catalog-import",
    tags=["catalog-import"],
    dependencies=[Depends(require_admin)],
)


def _json_value(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _preview_payload(preview: CatalogPreview) -> dict:
    labor = [_json_value(asdict(item)) for item in preview.labor]
    parts = [_json_value(asdict(item)) for item in preview.parts]
    errors = [asdict(item) for item in preview.errors]
    return {
        "summary": {"labor": len(labor), "parts": len(parts), "errors": len(errors)},
        "labor": labor,
        "parts": parts,
        "errors": errors,
    }


async def _read_xlsx(file: UploadFile) -> bytes:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=422, detail="Debe cargar la plantilla XLSX de SmartDiag504."
        )
    content = await file.read()
    if not content or len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="El archivo está vacío o supera 10 MB.")
    return content


@router.get("/template")
def download_template(demo: bool = Query(default=False)) -> StreamingResponse:
    return StreamingResponse(
        BytesIO(build_catalog_workbook(include_demo=demo)),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": (
                'attachment; filename="smartdiag504_catalogo_demo.xlsx"'
                if demo
                else 'attachment; filename="smartdiag504_catalogo_taller.xlsx"'
            )
        },
    )


@router.post("/preview")
async def preview_catalog(file: UploadFile = File(...)) -> dict:
    content = await _read_xlsx(file)
    scan_bytes(content, settings=get_settings())
    return _preview_payload(parse_catalog_workbook(content))


@router.post("/apply")
async def apply_catalog(
    file: UploadFile = File(...), settings: Settings = Depends(get_settings)
) -> dict:
    content = await _read_xlsx(file)
    scan_bytes(content, settings=settings)
    preview = parse_catalog_workbook(content)
    if preview.errors:
        raise HTTPException(status_code=422, detail=_preview_payload(preview))
    result = FrappeWriteClient(settings).import_workshop_catalog(_preview_payload(preview))
    return {"status": "applied", "summary": _preview_payload(preview)["summary"], "erpnext": result}
