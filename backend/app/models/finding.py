"""Modelo de dominio: Hallazgo."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.utils.enums import FindingStatus, RiskLevel


class NormativeRef(BaseModel):
    """Referencia a un control normativo (COBIT / COSO / RGSI)."""
    code: str
    title: str
    domain: Optional[str] = None       # COBIT: dominio (APO, BAI, DSS…)
    component: Optional[str] = None    # COSO: componente
    section: Optional[str] = None      # RGSI: capítulo/sección


class Evidence(BaseModel):
    """Evidencia documental que sustenta el hallazgo."""
    doc_id: str = Field(alias="docId")
    doc_name: str = Field(alias="docName")
    page: Optional[int] = None
    paragraph: Optional[str] = None

    model_config = {"populate_by_name": True}


class Finding(BaseModel):
    """Representa audits/{auditId}/findings/{findingId} en Firestore."""

    id: str
    audit_id: str = Field(alias="auditId")
    title: str
    description_finding: str = Field(default="", alias="descriptionFinding")
    criteria_description: str = Field(default="", alias="criteriaDescription")
    cause: str = Field(default="")
    effect: str = Field(default="")
    conclusion: str = Field(default="")
    description: str
    recommendation: str
    risk: RiskLevel
    risk_level: str = Field(default="", alias="riskLevel")
    impact: int = Field(ge=1, le=5)
    probability: int = Field(ge=1, le=5)
    status: FindingStatus = FindingStatus.PENDIENTE
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    cobit_refs: List[NormativeRef] = Field(default_factory=list, alias="cobitRef")
    coso_refs: List[NormativeRef] = Field(default_factory=list, alias="cosoRef")
    rgsi_refs: List[NormativeRef] = Field(default_factory=list, alias="rgsiRef")
    evidence: List[Evidence] = Field(default_factory=list)
    quote: Optional[str] = None
    detected_by: str = Field(default="COSFI-AI", alias="detectedBy")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")

    model_config = {"populate_by_name": True}

    def to_firestore(self) -> dict:
        return {
            "auditId": self.audit_id,
            "title": self.title,
            "descriptionFinding": self.description_finding,
            "criteriaDescription": self.criteria_description,
            "cause": self.cause,
            "effect": self.effect,
            "conclusion": self.conclusion,
            "description": self.description,
            "recommendation": self.recommendation,
            "risk": self.risk.value,
            "riskLevel": self.risk_level or self.risk.value,
            "impact": self.impact,
            "probability": self.probability,
            "status": self.status.value,
            "confidence": self.confidence,
            "cobitRef": [r.model_dump(exclude_none=True) for r in self.cobit_refs],
            "cosoRef": [r.model_dump(exclude_none=True) for r in self.coso_refs],
            "rgsiRef": [r.model_dump(exclude_none=True) for r in self.rgsi_refs],
            "evidence": [e.model_dump(by_alias=True, exclude_none=True) for e in self.evidence],
            "quote": self.quote,
            "detectedBy": self.detected_by,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_firestore(cls, doc_id: str, audit_id: str, data: dict) -> "Finding":
        def parse_refs(raw: Any) -> list:
            if not raw:
                return []
            if isinstance(raw, dict):
                raw = [raw]
            return [NormativeRef(**r) for r in raw if isinstance(r, dict)]

        def parse_evidence(raw: Any) -> list:
            if not raw:
                return []
            if isinstance(raw, dict):
                raw = [raw]

            evidence = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                try:
                    evidence.append(Evidence.model_validate(item))
                except Exception:
                    continue
            return evidence

        return cls(
            id=doc_id,
            auditId=audit_id,
            title=data.get("title", ""),
            description_finding=data.get("descriptionFinding", data.get("description", "")),
            criteria_description=data.get("criteriaDescription", ""),
            cause=data.get("cause", ""),
            effect=data.get("effect", ""),
            conclusion=data.get("conclusion", ""),
            description=data.get("description", ""),
            recommendation=data.get("recommendation", ""),
            risk=data.get("risk", RiskLevel.MEDIO),
            risk_level=data.get("riskLevel", data.get("risk", RiskLevel.MEDIO)),
            impact=data.get("impact", 3),
            probability=data.get("probability", 3),
            status=data.get("status", FindingStatus.PENDIENTE),
            confidence=data.get("confidence", 0.0),
            cobitRef=parse_refs(data.get("cobitRef")),
            cosoRef=parse_refs(data.get("cosoRef")),
            rgsiRef=parse_refs(data.get("rgsiRef")),
            evidence=parse_evidence(data.get("evidence")),
            quote=data.get("quote"),
            detectedBy=data.get("detectedBy", "COSFI-AI"),
            createdAt=data.get("createdAt", ""),
            updatedAt=data.get("updatedAt"),
        )
