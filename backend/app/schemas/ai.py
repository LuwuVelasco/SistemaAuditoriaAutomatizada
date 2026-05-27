"""Schemas para la capa IA — entradas al orquestador y salidas de los motores."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AIEngineResult(BaseModel):
    """Salida estándar de cada motor IA (COSO / COBIT / RGSI)."""
    framework: str
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0
    engine_version: str = "gemini-2.0-flash"


class RawFinding(BaseModel):
    """Hallazgo crudo producido por un motor antes de consolidación."""
    title: str
    description_finding: str = ""
    criteria_description: str = ""
    cause: str = ""
    effect: str = ""
    conclusion: str = ""
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: str = "Medio"
    cobit_refs: List[Dict] = Field(default_factory=list)
    coso_refs: List[Dict] = Field(default_factory=list)
    rgsi_refs: List[Dict] = Field(default_factory=list)
    evidence: List[Dict] = Field(default_factory=list)
    quote: Optional[str] = None
    source_framework: str = ""


class AnalysisRequest(BaseModel):
    """Petición al orquestador desde la API."""
    audit_id: str
    document_ids: Optional[List[str]] = None    # None = todos los docs del audit
