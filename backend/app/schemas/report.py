"""Schemas de entrada/salida para reportes."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import ReportFormat, ReportKind


class ReportGenerateRequest(BaseModel):
    kinds: List[ReportKind] = Field(min_length=1)
    format: ReportFormat = ReportFormat.XLSX


class ReportEmailRequest(BaseModel):
    report_ids: List[str] = Field(min_length=1)
    recipient_email: str


class ReportOut(BaseModel):
    id: str
    audit_id: str = Field(alias="auditId")
    kind: ReportKind
    format: ReportFormat
    supabase_path: str = Field(alias="supabasePath")
    sha256: Optional[str] = None
    generated_at: str = Field(alias="generatedAt")
    model_config = {"populate_by_name": True}
