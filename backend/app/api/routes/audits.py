"""
Rutas CRUD para auditorías + disparo del pipeline IA.
POST /api/v1/audits/{id}/analyze → BackgroundTask no bloqueante.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.deps import (
    CurrentUID,
    get_ai_service,
    get_audit_service,
)
from app.core.responses import created, ok
from app.schemas.audit import AuditCreate, AuditOut, AuditUpdate
from app.services.ai_service import AIService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audits", tags=["audits"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_audit(
    body: AuditCreate,
    uid: CurrentUID,
    svc: AuditService = Depends(get_audit_service),
):
    audit = await svc.create(body, uid)
    return created(AuditOut.model_validate(audit.to_firestore() | {"id": audit.id}).model_dump(by_alias=True))


@router.get("")
async def list_audits(
    uid: CurrentUID,
    svc: AuditService = Depends(get_audit_service),
):
    audits = await svc.list_by_owner(uid)
    return ok([AuditOut.model_validate(a.to_firestore() | {"id": a.id}).model_dump(by_alias=True) for a in audits])


@router.get("/{audit_id}")
async def get_audit(
    audit_id: str,
    uid: CurrentUID,
    svc: AuditService = Depends(get_audit_service),
):
    audit = await svc.get_by_id(audit_id, uid)
    return ok(AuditOut.model_validate(audit.to_firestore() | {"id": audit.id}).model_dump(by_alias=True))


@router.patch("/{audit_id}")
async def update_audit(
    audit_id: str,
    body: AuditUpdate,
    uid: CurrentUID,
    svc: AuditService = Depends(get_audit_service),
):
    audit = await svc.update(audit_id, body, uid)
    return ok(AuditOut.model_validate(audit.to_firestore() | {"id": audit.id}).model_dump(by_alias=True))


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(
    audit_id: str,
    uid: CurrentUID,
    svc: AuditService = Depends(get_audit_service),
):
    await svc.delete(audit_id, uid)


@router.post("/{audit_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_audit(
    audit_id: str,
    background_tasks: BackgroundTasks,
    uid: CurrentUID,
    audit_svc: AuditService = Depends(get_audit_service),
    ai_svc: AIService = Depends(get_ai_service),
):
    """
    Dispara el pipeline IA en segundo plano.
    Verifica propiedad antes de encolar la tarea.
    """
    await audit_svc.get_by_id(audit_id, uid)   # valida owner
    background_tasks.add_task(ai_svc.run_analysis, audit_id)
    return ok({"message": "Análisis IA iniciado.", "auditId": audit_id})
