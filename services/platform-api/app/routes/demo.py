from fastapi import APIRouter, Depends

from app.auth import require_admin
from app.demo_data import DEMO_LABOR, DEMO_PARTS, DEMO_VEHICLES

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.get("/catalog")
def demo_catalog() -> dict[str, object]:
    """Return the non-sensitive catalog fixture used by the staging demo."""
    public_parts = [
        {key: value for key, value in part.items() if key != "cost"} for part in DEMO_PARTS
    ]
    public_labor = [
        {key: value for key, value in labor.items() if key != "cost"} for labor in DEMO_LABOR
    ]
    return {"vehicles": DEMO_VEHICLES, "labor": public_labor, "parts": public_parts}


@router.get("/warehouse", dependencies=[Depends(require_admin)])
def demo_warehouse() -> dict[str, object]:
    """Expose internal demo picking data to authenticated operations clients."""
    return {"parts": DEMO_PARTS}
