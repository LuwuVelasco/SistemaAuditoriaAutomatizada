"""Modelo de dominio: Documento cargado."""

from typing import Optional

from pydantic import BaseModel, Field

from app.utils.enums import DocumentStatus


class Document(BaseModel):
    """Representa audits/{auditId}/documents/{docId} en Firestore."""

    id: str
    audit_id: str = Field(alias="auditId")
    name: str
    type: str                          # pdf | docx | xlsx
    size: str                          # "2.4 MB"
    supabase_path: str = Field(alias="supabasePath")
    status: DocumentStatus = DocumentStatus.QUEUED
    chunks: int = 0
    sha256: Optional[str] = None
    uploaded_at: str = Field(alias="uploadedAt")

    model_config = {"populate_by_name": True}

    def to_firestore(self) -> dict:
        return {
            "auditId": self.audit_id,
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "supabasePath": self.supabase_path,
            "status": self.status.value,
            "chunks": self.chunks,
            "sha256": self.sha256,
            "uploadedAt": self.uploaded_at,
        }

    @classmethod
    def from_firestore(cls, doc_id: str, audit_id: str, data: dict) -> "Document":
        return cls(
            id=doc_id,
            auditId=audit_id,
            name=data.get("name", ""),
            type=data.get("type", ""),
            size=data.get("size", ""),
            supabasePath=data.get("supabasePath", ""),
            status=data.get("status", DocumentStatus.QUEUED),
            chunks=data.get("chunks", 0),
            sha256=data.get("sha256"),
            uploadedAt=data.get("uploadedAt", ""),
        )
