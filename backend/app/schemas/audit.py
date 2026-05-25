"""Schemas de entrada/salida para auditorías."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.enums import AuditStatus, FrameworkType


class AuditCreate(BaseModel):
    entity: str = Field(min_length=2, max_length=120)
    type: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=60)
    period: str = Field(pattern=r"^\d{4}-Q[1-4]$", examples=["2025-Q1"])
    frameworks: List[FrameworkType] = Field(min_length=1)

    @field_validator("entity", "type", "city", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip()


class AuditUpdate(BaseModel):
    entity: Optional[str] = None
    type: Optional[str] = None
    city: Optional[str] = None
    period: Optional[str] = None
    status: Optional[AuditStatus] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    frameworks: Optional[List[FrameworkType]] = None


class AuditOut(BaseModel):
    id: str
    entity: str
    type: str
    city: str
    period: str
    status: AuditStatus
    progress: int
    frameworks: List[str]
    owner_id: str = Field(alias="ownerId")
    created_at: str = Field(alias="createdAt")
    findings_count: int = Field(default=0, alias="findingsCount")
    pending_findings: int = Field(default=0, alias="pendingFindings")
    documents_count: int = Field(default=0, alias="documentsCount")

    model_config = {"populate_by_name": True}
