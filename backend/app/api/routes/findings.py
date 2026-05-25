"""
Rutas CRUD para hallazgos de una auditoría, incluyendo historial de cambios.
"""

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUID, get_finding_service, get_history_service
from app.core.responses import created, ok
from app.schemas.finding import FindingCreate, FindingOut, FindingUpdate
from app.services.finding_service import FindingService
from app.services.history_service import HistoryService

router = APIRouter(prefix="/audits/{audit_id}/findings", tags=["findings"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_finding(
    audit_id: str,
    body: FindingCreate,
    uid: CurrentUID,
    svc: FindingService = Depends(get_finding_service),
):
    finding = await svc.create(audit_id, body, uid)
    return created(_finding_out(finding))


@router.get("")
async def list_findings(
    audit_id: str,
    uid: CurrentUID,
    svc: FindingService = Depends(get_finding_service),
):
    findings = await svc.list_by_audit(audit_id, uid)
    return ok([_finding_out(f) for f in findings])


@router.get("/{finding_id}")
async def get_finding(
    audit_id: str,
    finding_id: str,
    uid: CurrentUID,
    svc: FindingService = Depends(get_finding_service),
):
    finding = await svc.get_by_id(audit_id, finding_id, uid)
    return ok(_finding_out(finding))


@router.patch("/{finding_id}")
async def update_finding(
    audit_id: str,
    finding_id: str,
    body: FindingUpdate,
    uid: CurrentUID,
    svc: FindingService = Depends(get_finding_service),
):
    finding = await svc.update(audit_id, finding_id, body, uid)
    return ok(_finding_out(finding))


@router.delete("/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(
    audit_id: str,
    finding_id: str,
    uid: CurrentUID,
    svc: FindingService = Depends(get_finding_service),
):
    await svc.delete(audit_id, finding_id, uid)


@router.get("/{finding_id}/history")
async def get_finding_history(
    audit_id: str,
    finding_id: str,
    uid: CurrentUID,
    finding_svc: FindingService = Depends(get_finding_service),
    history_svc: HistoryService = Depends(get_history_service),
):
    # Verificar acceso antes de exponer historial
    await finding_svc.get_by_id(audit_id, finding_id, uid)
    events = await history_svc.get_history(audit_id, finding_id)
    return ok(events)


def _finding_out(finding) -> dict:
    data = finding.to_firestore()
    data["id"] = finding.id
    return FindingOut.model_validate(data).model_dump(by_alias=True)
