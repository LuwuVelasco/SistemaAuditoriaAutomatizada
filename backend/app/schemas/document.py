"""Schemas de entrada/salida para documentos."""

from typing import Optional

from pydantic import BaseModel, Field

from app.utils.enums import DocumentStatus


class DocumentOut(BaseModel):
    id: str
    audit_id: str = Field(alias="auditId")
    name: str
    type: str
    size: str
    supabase_path: str = Field(alias="supabasePath")
    status: DocumentStatus
    chunks: int
    sha256: Optional[str] = None
    uploaded_at: str = Field(alias="uploadedAt")
    model_config = {"populate_by_name": True}
