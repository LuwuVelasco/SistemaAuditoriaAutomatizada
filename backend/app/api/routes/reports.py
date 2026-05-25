"""
Rutas para generación y listado de reportes de auditoría.
"""

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUID, get_report_service
from app.core.responses import created, ok
from app.schemas.report import ReportGenerateRequest, ReportOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/audits/{audit_id}/reports", tags=["reports"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def generate_reports(
    audit_id: str,
    body: ReportGenerateRequest,
    uid: CurrentUID,
    svc: ReportService = Depends(get_report_service),
):
    """Genera uno o más reportes para la auditoría y los sube a Supabase Storage."""
    reports = await svc.generate(audit_id, uid, body)
    return created([_report_out(r) for r in reports])


@router.get("")
async def list_reports(
    audit_id: str,
    uid: CurrentUID,
    svc: ReportService = Depends(get_report_service),
):
    reports = await svc.list_by_audit(audit_id, uid)
    return ok([_report_out(r) for r in reports])


def _report_out(report) -> dict:
    data = report.to_firestore()
    data["id"] = report.id
    return ReportOut.model_validate(data).model_dump(by_alias=True)
