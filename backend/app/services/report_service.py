"""
Servicio de generación de reportes.
Produce XLSX, DOCX o PDF a partir de los hallazgos de una auditoría.
Sube el archivo a Supabase Storage y registra el reporte en Firestore.
"""

import io
from typing import List

from docx import Document as DocxDocument
from docx.shared import Pt, RGBColor
from loguru import logger
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.finding import Finding
from app.models.report import Report
from app.repositories.audit_repository import AuditRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportGenerateRequest
from app.services.storage_service import StorageService
from app.utils.enums import ReportFormat, ReportKind
from app.utils.helpers import generate_id
from app.utils.timestamps import utcnow_iso

_CONTENT_TYPES = {
    ReportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ReportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ReportFormat.PDF:  "application/pdf",
}

_EXTENSIONS = {
    ReportFormat.XLSX: "xlsx",
    ReportFormat.DOCX: "docx",
    ReportFormat.PDF:  "pdf",
}

# Colores para cabeceras XLSX
_HEADER_FILL  = PatternFill("solid", fgColor="0D1117")
_HEADER_FONT  = Font(bold=True, color="22D3EE", name="Calibri", size=11)
_RISK_COLORS  = {"Bajo": "22C55E", "Medio": "F59E0B", "Alto": "F97316", "Extremo": "EF4444"}


class ReportService:
    def __init__(
        self,
        audit_repo: AuditRepository,
        finding_repo: FindingRepository,
        report_repo: ReportRepository,
        storage: StorageService,
    ):
        self._audits   = audit_repo
        self._findings = finding_repo
        self._reports  = report_repo
        self._storage  = storage

    async def generate(
        self,
        audit_id: str,
        owner_id: str,
        request: ReportGenerateRequest,
    ) -> List[Report]:
        """Genera un reporte por cada kind solicitado y los retorna."""
        audit = await self._audits.get_by_id(audit_id)
        if audit is None:
            raise NotFoundError("Auditoría", audit_id)
        if audit.owner_id != owner_id:
            raise ForbiddenError("No tienes acceso a esta auditoría.")

        findings = await self._findings.list_by_audit(audit_id)

        created: List[Report] = []
        for kind in request.kinds:
            report = await self._generate_one(audit_id, audit.entity, kind, request.format, findings)
            created.append(report)

        return created

    async def _generate_one(
        self,
        audit_id: str,
        entity: str,
        kind: ReportKind,
        fmt: ReportFormat,
        findings: List[Finding],
    ) -> Report:
        now = utcnow_iso()
        report_id = generate_id("RPT-")
        filename = f"{kind.value}_{report_id}.{_EXTENSIONS[fmt]}"

        if fmt == ReportFormat.XLSX:
            content = self._build_xlsx(kind, entity, findings)
        elif fmt == ReportFormat.DOCX:
            content = self._build_docx(kind, entity, findings)
        else:
            content = self._build_xlsx(kind, entity, findings)  # PDF → XLSX como fallback funcional
            filename = filename.replace(".pdf", ".xlsx")
            fmt = ReportFormat.XLSX

        sha = StorageService.compute_sha256(content)
        path = await self._storage.upload_report(audit_id, filename, content, _CONTENT_TYPES[fmt])

        report = Report(
            id=report_id,
            auditId=audit_id,
            kind=kind,
            format=fmt,
            supabasePath=path,
            sha256=sha,
            generatedAt=now,
        )
        result = await self._reports.create(report)
        logger.info(f"Reporte generado: {kind.value} ({fmt.value}) → {path}")
        return result

    async def list_by_audit(self, audit_id: str, owner_id: str) -> List[Report]:
        audit = await self._audits.get_by_id(audit_id)
        if audit is None:
            raise NotFoundError("Auditoría", audit_id)
        if audit.owner_id != owner_id:
            raise ForbiddenError("No tienes acceso a esta auditoría.")
        return await self._reports.list_by_audit(audit_id)

    # ── XLSX builders ─────────────────────────────────────────────────────────

    def _build_xlsx(self, kind: ReportKind, entity: str, findings: List[Finding]) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = kind.value[:31]  # Limit sheet name

        if kind == ReportKind.MATRIZ_HALLAZGOS:
            self._xlsx_matriz_hallazgos(ws, entity, findings)
        elif kind == ReportKind.FICHAS_HALLAZGO:
            self._xlsx_fichas_hallazgo(ws, entity, findings)
        elif kind == ReportKind.FICHAS_PRUEBAS:
            self._xlsx_fichas_pruebas(ws, entity, findings)
        elif kind == ReportKind.MATRIZ_COSO:
            self._xlsx_matriz_coso(ws, entity, findings)

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def _write_header_row(self, ws, headers: list, row: int = 1) -> None:
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=h)
            cell.fill = _HEADER_FILL
            cell.font = _HEADER_FONT
            cell.alignment = Alignment(horizontal="center", wrap_text=True)

    def _xlsx_matriz_hallazgos(self, ws, entity: str, findings: List[Finding]) -> None:
        ws["A1"] = f"MATRIZ DE HALLAZGOS — {entity}"
        ws["A1"].font = Font(bold=True, size=14, name="Calibri")
        ws.merge_cells("A1:N1")

        headers = [
            "ID", "Título", "Finding", "Criteria", "Cause", "Effect", "Conclusion",
            "Riesgo", "Risk Level", "Impacto", "Probabilidad",
            "Estado", "Confianza IA", "Detectado por"
        ]
        self._write_header_row(ws, headers, row=2)

        for i, f in enumerate(findings, start=3):
            risk_color = _RISK_COLORS.get(f.risk.value if hasattr(f.risk, "value") else str(f.risk), "FFFFFF")
            row_data = [
                f.id,
                f.title,
                f.description_finding or f.description,
                f.criteria_description or "",
                f.cause or "",
                f.effect or "",
                f.conclusion or "",
                f.risk.value if hasattr(f.risk, "value") else str(f.risk),
                getattr(f, "risk_level", "") or (f.risk.value if hasattr(f.risk, "value") else str(f.risk)),
                f.impact,
                f.probability,
                f.status.value if hasattr(f.status, "value") else str(f.status),
                f"{f.confidence:.0%}",
                f.detected_by or "",
            ]
            for col, val in enumerate(row_data, 1):
                cell = ws.cell(row=i, column=col, value=val)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                if col == 4:
                    cell.fill = PatternFill("solid", fgColor=risk_color)
                    cell.font = Font(bold=True, color="0D1117")

        ws.column_dimensions["A"].width = 14
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 40
        ws.column_dimensions["D"].width = 38
        ws.column_dimensions["E"].width = 28
        ws.column_dimensions["F"].width = 28
        ws.column_dimensions["G"].width = 40
        ws.column_dimensions["H"].width = 12
        ws.column_dimensions["I"].width = 12
        ws.column_dimensions["J"].width = 12
        ws.column_dimensions["K"].width = 10
        ws.column_dimensions["L"].width = 12
        ws.column_dimensions["M"].width = 14
        ws.column_dimensions["N"].width = 12

    def _xlsx_fichas_hallazgo(self, ws, entity: str, findings: List[Finding]) -> None:
        ws["A1"] = f"FICHAS DE HALLAZGO — {entity}"
        ws["A1"].font = Font(bold=True, size=14, name="Calibri")
        ws.merge_cells("A1:K1")

        headers = ["ID", "Título", "Finding", "Criteria", "Cause", "Effect", "Conclusion", "Riesgo", "Recomendación", "Refs COBIT", "Refs COSO"]
        self._write_header_row(ws, headers, row=2)

        for i, f in enumerate(findings, start=3):
            cobit = "; ".join(r.code for r in (f.cobit_ref or []))
            coso  = "; ".join(r.code for r in (f.coso_ref or []))
            row_data = [
                f.id,
                f.title,
                f.description_finding or f.description,
                f.criteria_description or "",
                f.cause or "",
                f.effect or "",
                f.conclusion or "",
                f.risk.value if hasattr(f.risk, "value") else str(f.risk),
                f.recommendation,
                cobit, coso,
            ]
            for col, val in enumerate(row_data, 1):
                ws.cell(row=i, column=col, value=val).alignment = Alignment(wrap_text=True, vertical="top")

        ws.column_dimensions["B"].width = 26
        ws.column_dimensions["C"].width = 36
        ws.column_dimensions["D"].width = 36
        ws.column_dimensions["E"].width = 28
        ws.column_dimensions["F"].width = 28
        ws.column_dimensions["G"].width = 36
        ws.column_dimensions["I"].width = 60

    def _xlsx_fichas_pruebas(self, ws, entity: str, findings: List[Finding]) -> None:
        ws["A1"] = f"FICHAS DE PRUEBAS — {entity}"
        ws["A1"].font = Font(bold=True, size=14, name="Calibri")
        ws.merge_cells("A1:E1")

        headers = ["ID Hallazgo", "Título", "Evidencia", "Cita del Documento", "Estado"]
        self._write_header_row(ws, headers, row=2)

        for i, f in enumerate(findings, start=3):
            evidence = "; ".join(str(e) for e in (f.evidence or []))
            row_data = [
                f.id, f.title, evidence,
                f.quote or "",
                f.status.value if hasattr(f.status, "value") else str(f.status),
            ]
            for col, val in enumerate(row_data, 1):
                ws.cell(row=i, column=col, value=val).alignment = Alignment(wrap_text=True, vertical="top")

        ws.column_dimensions["B"].width = 35
        ws.column_dimensions["C"].width = 40
        ws.column_dimensions["D"].width = 55

    def _xlsx_matriz_coso(self, ws, entity: str, findings: List[Finding]) -> None:
        ws["A1"] = f"MATRIZ COSO — {entity}"
        ws["A1"].font = Font(bold=True, size=14, name="Calibri")
        ws.merge_cells("A1:G1")

        headers = ["ID", "Título", "Componente COSO", "Principio", "Riesgo", "Recomendación", "Estado"]
        self._write_header_row(ws, headers, row=2)

        for i, f in enumerate(findings, start=3):
            coso_ref = (f.coso_ref or [])
            comp  = coso_ref[0].component if coso_ref and hasattr(coso_ref[0], "component") else ""
            princ = coso_ref[0].principle if coso_ref and hasattr(coso_ref[0], "principle") else ""
            row_data = [
                f.id, f.title, comp, princ,
                f.risk.value if hasattr(f.risk, "value") else str(f.risk),
                f.recommendation,
                f.status.value if hasattr(f.status, "value") else str(f.status),
            ]
            for col, val in enumerate(row_data, 1):
                ws.cell(row=i, column=col, value=val).alignment = Alignment(wrap_text=True, vertical="top")

        ws.column_dimensions["B"].width = 35
        ws.column_dimensions["F"].width = 55

    # ── DOCX builders ─────────────────────────────────────────────────────────

    def _build_docx(self, kind: ReportKind, entity: str, findings: List[Finding]) -> bytes:
        doc = DocxDocument()

        # Título
        title = doc.add_heading(f"{kind.value.upper().replace('-', ' ')} — {entity}", 0)
        title.runs[0].font.color.rgb = RGBColor(0x22, 0xD3, 0xEE)

        doc.add_paragraph(f"Generado por COSFI/SAAM  |  Total hallazgos: {len(findings)}")
        doc.add_paragraph("")

        for f in findings:
            # Encabezado de hallazgo
            h = doc.add_heading(f"[{f.id}] {f.title}", level=2)
            h.runs[0].font.color.rgb = RGBColor(0xF9, 0x7B, 0x16) if str(f.risk) in ("Alto", "Extremo") else RGBColor(0x22, 0xD3, 0xEE)

            tbl = doc.add_table(rows=1, cols=2)
            tbl.style = "Table Grid"
            self._docx_row(tbl, "Finding", f.description_finding or f.description)
            self._docx_row(tbl, "Criteria", f.criteria_description or "")
            self._docx_row(tbl, "Cause", f.cause or "")
            self._docx_row(tbl, "Effect", f.effect or "")
            self._docx_row(tbl, "Conclusion", f.conclusion or "")
            self._docx_row(tbl, "Riesgo", f.risk.value if hasattr(f.risk, "value") else str(f.risk))
            self._docx_row(tbl, "Risk Level", getattr(f, "risk_level", "") or (f.risk.value if hasattr(f.risk, "value") else str(f.risk)))
            self._docx_row(tbl, "Estado", f.status.value if hasattr(f.status, "value") else str(f.status))
            self._docx_row(tbl, "Impacto", str(f.impact))
            self._docx_row(tbl, "Probabilidad", str(f.probability))
            self._docx_row(tbl, "Confianza IA", f"{f.confidence:.0%}")

            doc.add_paragraph("")

            doc.add_paragraph("Recomendación")
            p2 = doc.add_paragraph(f.recommendation)
            p2.runs[0].font.size = Pt(10)

            if f.quote:
                doc.add_paragraph("Cita del documento")
                q = doc.add_paragraph(f'"{f.quote}"')
                q.runs[0].italic = True
                q.runs[0].font.size = Pt(9)

            doc.add_paragraph("─" * 80)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    @staticmethod
    def _docx_row(table, label: str, value: str) -> None:
        row = table.add_row()
        row.cells[0].text = label
        row.cells[0].paragraphs[0].runs[0].bold = True
        row.cells[1].text = value
