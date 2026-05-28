"""Modelo de dominio: Reporte generado."""

from typing import Optional

from pydantic import BaseModel, Field

from app.utils.enums import ReportFormat, ReportKind


class Report(BaseModel):
    """Representa audits/{auditId}/reports/{reportId} en Firestore."""

    id: str
    audit_id: str = Field(alias="auditId")
    kind: ReportKind
    format: ReportFormat
    supabase_path: str = Field(alias="supabasePath")
    sha256: Optional[str] = None
    generated_at: str = Field(alias="generatedAt")

    model_config = {"populate_by_name": True}

    def to_firestore(self) -> dict:
        return {
            "auditId": self.audit_id,
            "kind": self.kind.value,
            "format": self.format.value,
            "supabasePath": self.supabase_path,
            "sha256": self.sha256,
            "generatedAt": self.generated_at,
        }

    @classmethod
    def from_firestore(cls, doc_id: str, audit_id: str, data: dict) -> "Report":
        return cls(
            id=doc_id,
            auditId=audit_id,
            kind=data.get("kind", ReportKind.MATRIZ_HALLAZGOS),
            format=data.get("format", ReportFormat.XLSX),
            supabasePath=data.get("supabasePath", ""),
            sha256=data.get("sha256"),
            generatedAt=data.get("generatedAt", ""),
        )
