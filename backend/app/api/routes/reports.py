"""
Rutas para generación y listado de reportes de auditoría.
"""

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import CurrentUID, get_report_service
from app.core.responses import created, ok
from app.core.config import settings
from app.schemas.report import ReportGenerateRequest, ReportOut
from app.services.report_service import ReportService
from app.services.storage_service import StorageService
from app.api.deps import get_storage

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


@router.get("/{report_id}/download")
async def download_report(
    audit_id: str,
    report_id: str,
    uid: CurrentUID,
    svc: ReportService = Depends(get_report_service),
    storage: StorageService = Depends(get_storage),
):
    """Descarga un reporte existente desde Supabase Storage."""
    report = await svc.get_by_id(audit_id, report_id, uid)

    bucket = settings.SUPABASE_BUCKET_XLSX
    content = await storage.download_file(bucket, report.supabase_path)
    filename = report.supabase_path.rsplit("/", 1)[-1] or f"{report.kind.value}.{report.format.value}"

    content_type = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
    }.get(report.format.value, "application/octet-stream")

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _report_out(report) -> dict:
    data = report.to_firestore()
    data["id"] = report.id
    return ReportOut.model_validate(data).model_dump(by_alias=True)
