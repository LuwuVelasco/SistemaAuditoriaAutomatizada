"""Schemas de entrada/salida para hallazgos."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.enums import FindingStatus, RiskLevel


class NormativeRefIn(BaseModel):
    code: str
    title: str
    domain: Optional[str] = None
    component: Optional[str] = None
    section: Optional[str] = None


class EvidenceIn(BaseModel):
    doc_id: str = Field(alias="docId")
    doc_name: str = Field(alias="docName")
    page: Optional[int] = None
    paragraph: Optional[str] = None
    model_config = {"populate_by_name": True}


class FindingCreate(BaseModel):
    title: str = Field(min_length=5)
    description_finding: str = Field(default="")
    criteria_description: str = Field(default="")
    cause: str = Field(default="")
    effect: str = Field(default="")
    conclusion: str = Field(default="")
    description: str = Field(min_length=10)
    recommendation: str = Field(min_length=10)
    impact: int = Field(ge=1, le=5)
    probability: int = Field(ge=1, le=5)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    cobit_refs: List[NormativeRefIn] = Field(default_factory=list, alias="cobitRef")
    coso_refs: List[NormativeRefIn] = Field(default_factory=list, alias="cosoRef")
    rgsi_refs: List[NormativeRefIn] = Field(default_factory=list, alias="rgsiRef")
    evidence: List[EvidenceIn] = Field(default_factory=list)
    quote: Optional[str] = None
    detected_by: str = Field(default="COSFI-AI", alias="detectedBy")
    model_config = {"populate_by_name": True}


class FindingUpdate(BaseModel):
    title: Optional[str] = None
    description_finding: Optional[str] = None
    criteria_description: Optional[str] = None
    cause: Optional[str] = None
    effect: Optional[str] = None
    conclusion: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    impact: Optional[int] = Field(default=None, ge=1, le=5)
    probability: Optional[int] = Field(default=None, ge=1, le=5)
    status: Optional[FindingStatus] = None
    cobit_refs: Optional[List[NormativeRefIn]] = Field(default=None, alias="cobitRef")
    coso_refs: Optional[List[NormativeRefIn]] = Field(default=None, alias="cosoRef")
    rgsi_refs: Optional[List[NormativeRefIn]] = Field(default=None, alias="rgsiRef")
    evidence: Optional[List[EvidenceIn]] = None
    quote: Optional[str] = None
    model_config = {"populate_by_name": True}


class FindingOut(BaseModel):
    id: str
    audit_id: str = Field(alias="auditId")
    title: str
    description_finding: str = Field(default="", alias="descriptionFinding")
    criteria_description: str = Field(default="", alias="criteriaDescription")
    cause: str = ""
    effect: str = ""
    conclusion: str = ""
    description: str
    recommendation: str
    risk: RiskLevel
    impact: int
    probability: int
    risk_level: str = Field(default="", alias="riskLevel")
    status: FindingStatus
    confidence: float
    cobit_refs: List[Dict] = Field(default_factory=list, alias="cobitRef")
    coso_refs: List[Dict] = Field(default_factory=list, alias="cosoRef")
    rgsi_refs: List[Dict] = Field(default_factory=list, alias="rgsiRef")
    evidence: List[Dict] = Field(default_factory=list)
    quote: Optional[str] = None
    detected_by: str = Field(alias="detectedBy")
    created_at: str = Field(alias="createdAt")
    updated_at: Optional[str] = Field(default=None, alias="updatedAt")
    model_config = {"populate_by_name": True}
