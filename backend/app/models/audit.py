"""Modelo de dominio: Auditoría."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import AuditStatus, FrameworkType


DEFAULT_MATURITY = {
    "level": 1,
    "scores": {
        "policies": 20,
        "processes": 10,
        "traceability": 15,
        "culture": 5
    },
    "checklist": {
        "l1_repositorios": True, "l1_sin_politicas": True,
        "l2_cuadro": False, "l2_calendario": False, "l2_desigual": True,
        "l3_procesos": False, "l3_roles": False, "l3_trazabilidad": False,
        "l4_riesgos": False, "l4_activos": False, "l4_coordinacion": False,
        "l5_cultura": False, "l5_mejora": False, "l5_inspeccion": False
    },
    "gapAnalysis": {
        "strengths": ["Existen repositorios digitales para almacenamiento de archivos."],
        "weaknesses": ["Ausencia de políticas documentales aprobadas formalmente.", "Falta de un cuadro de clasificación archivística."],
        "roadmap": ["Diseñar y formalizar un Cuadro de Clasificación Documental básico.", "Definir responsables funcionales y técnicos de gestión de archivos."]
    }
}


class Audit(BaseModel):
    """Representa un documento audits/{auditId} en Firestore."""

    id: str
    entity: str
    type: str
    city: str
    period: str
    alcance: Optional[str] = None
    status: AuditStatus = AuditStatus.PENDIENTE
    progress: int = Field(default=0, ge=0, le=100)
    frameworks: List[FrameworkType]
    owner_id: str = Field(alias="ownerId")
    created_at: str = Field(alias="createdAt")
    findings_count: int = Field(default=0, alias="findingsCount")
    pending_findings: int = Field(default=0, alias="pendingFindings")
    documents_count: int = Field(default=0, alias="documentsCount")
    maturity: Optional[dict] = None

    model_config = {"populate_by_name": True}

    def to_firestore(self) -> dict:
        """Serializa para Firestore (camelCase, sin campos nulos)."""
        d = {
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
        if self.alcance is not None:
            d["alcance"] = self.alcance
        if self.maturity is not None:
            d["maturity"] = self.maturity
        return d

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "Audit":
        return cls(
            id=doc_id,
            entity=data.get("entity", ""),
            type=data.get("type", ""),
            city=data.get("city", ""),
            period=data.get("period", ""),
            alcance=data.get("alcance"),
            status=data.get("status", AuditStatus.PENDIENTE),
            progress=data.get("progress", 0),
            frameworks=data.get("frameworks", []),
            ownerId=data.get("ownerId", ""),
            createdAt=data.get("createdAt", ""),
            findingsCount=data.get("findingsCount", 0),
            pendingFindings=data.get("pendingFindings", 0),
            documentsCount=data.get("documentsCount", 0),
            maturity=data.get("maturity", DEFAULT_MATURITY.copy()),
        )
