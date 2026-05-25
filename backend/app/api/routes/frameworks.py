"""
Rutas de catálogos normativos (COBIT, COSO, RGSI) — solo lectura.
No requieren autenticación estricta, pero se incluye token opcional para logs.
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUID, get_framework_service
from app.core.responses import ok
from app.services.framework_service import FrameworkService

router = APIRouter(prefix="/frameworks", tags=["frameworks"])


@router.get("/{framework}/controls")
async def list_controls(
    framework: str,
    uid: CurrentUID,
    svc: FrameworkService = Depends(get_framework_service),
):
    controls = await svc.list_controls(framework)
    return ok([c.model_dump() for c in controls])


@router.get("/{framework}/controls/{control_id}")
async def get_control(
    framework: str,
    control_id: str,
    uid: CurrentUID,
    svc: FrameworkService = Depends(get_framework_service),
):
    control = await svc.get_control(framework, control_id)
    if control is None:
        from app.core.exceptions import raise_not_found
        raise_not_found("Control", control_id)
    return ok(control.model_dump())


@router.get("/{framework}/search")
async def search_controls(
    framework: str,
    uid: CurrentUID,
    q: str = Query(..., min_length=2, description="Palabra clave a buscar"),
    svc: FrameworkService = Depends(get_framework_service),
):
    controls = await svc.search(framework, q)
    return ok([c.model_dump() for c in controls])
