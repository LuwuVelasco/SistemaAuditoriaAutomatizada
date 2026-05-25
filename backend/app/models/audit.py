"""Modelo de dominio: Auditoría."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import AuditStatus, FrameworkType


class Audit(BaseModel):
    """Representa un documento audits/{auditId} en Firestore."""

    id: str
    entity: str
    type: str
    city: str
    period: str
    status: AuditStatus = AuditStatus.PENDIENTE
    progress: int = Field(default=0, ge=0, le=100)
    frameworks: List[FrameworkType]
    owner_id: str = Field(alias="ownerId")
    created_at: str = Field(alias="createdAt")
    findings_count: int = Field(default=0, alias="findingsCount")
    pending_findings: int = Field(default=0, alias="pendingFindings")
    documents_count: int = Field(default=0, alias="documentsCount")

    model_config = {"populate_by_name": True}

    def to_firestore(self) -> dict:
        """Serializa para Firestore (camelCase, sin campos nulos)."""
        return {
            "entity": self.entity,
            "type": self.type,
            "city": self.city,
            "period": self.period,
            "status": self.status.value,
            "progress": self.progress,
            "frameworks": [f.value for f in self.frameworks],
            "ownerId": self.owner_id,
            "createdAt": self.created_at,
            "findingsCount": self.findings_count,
            "pendingFindings": self.pending_findings,
            "documentsCount": self.documents_count,
        }

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "Audit":
        return cls(
            id=doc_id,
            entity=data.get("entity", ""),
            type=data.get("type", ""),
            city=data.get("city", ""),
            period=data.get("period", ""),
            status=data.get("status", AuditStatus.PENDIENTE),
            progress=data.get("progress", 0),
            frameworks=data.get("frameworks", []),
            ownerId=data.get("ownerId", ""),
            createdAt=data.get("createdAt", ""),
            findingsCount=data.get("findingsCount", 0),
            pendingFindings=data.get("pendingFindings", 0),
            documentsCount=data.get("documentsCount", 0),
        )
