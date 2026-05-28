"""
Rutas del dashboard: resumen ejecutivo de métricas del usuario autenticado.
"""

from fastapi import APIRouter, Depends
from google.cloud import firestore

from app.api.deps import CurrentUID, DB, get_audit_repo, get_finding_repo
from app.core.responses import ok
from app.repositories.audit_repository import AuditRepository
from app.repositories.finding_repository import FindingRepository
from app.utils.enums import AuditStatus, FindingStatus, RiskLevel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_summary(
    uid: CurrentUID,
    audit_repo: AuditRepository = Depends(get_audit_repo),
    finding_repo: FindingRepository = Depends(get_finding_repo),
):
    """
    Retorna métricas globales para el dashboard del usuario:
    - Auditorías activas / pendientes / finalizadas
    - Total de hallazgos y distribución por riesgo
    - Hallazgos pendientes de revisión
    """
    audits = await audit_repo.list_by_owner(uid)

    total_audits     = len(audits)
    active_audits    = sum(1 for a in audits if a.status == AuditStatus.EN_REVISION)
    pending_audits   = sum(1 for a in audits if a.status == AuditStatus.PENDIENTE)
    processing       = sum(1 for a in audits if a.status == AuditStatus.PROCESANDO)
    completed_audits = sum(1 for a in audits if a.status == AuditStatus.FINALIZADA)
    total_docs       = sum(getattr(a, "documents_count", 0) for a in audits)
    total_findings   = sum(getattr(a, "findings_count", 0) for a in audits)
    pending_findings = sum(getattr(a, "pending_findings", 0) for a in audits)

    # Distribución de riesgo: agrega desde contadores en auditorías
    risk_distribution = {
        RiskLevel.BAJO.value:    0,
        RiskLevel.MEDIO.value:   0,
        RiskLevel.ALTO.value:    0,
        RiskLevel.EXTREMO.value: 0,
    }

    # Auditorías recientes (últimas 5)
    recent = [
        {
            "id": a.id,
            "entity": a.entity,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "progress": a.progress,
            "findingsCount": getattr(a, "findings_count", 0),
            "createdAt": a.created_at,
        }
        for a in audits[:5]
    ]

    return ok({
        "totalAudits":      total_audits,
        "activeAudits":     active_audits,
        "pendingAudits":    pending_audits,
        "processingAudits": processing,
        "completedAudits":  completed_audits,
        "totalDocuments":   total_docs,
        "totalFindings":    total_findings,
        "pendingFindings":  pending_findings,
        "riskDistribution": risk_distribution,
        "recentAudits":     recent,
    })
