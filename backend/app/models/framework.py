"""Modelo de dominio: Control normativo del catálogo."""

from typing import List, Optional

from pydantic import BaseModel, Field


class FrameworkControl(BaseModel):
    """Representa frameworks/{framework}/controls/{controlId} en Firestore."""

    id: str
    framework: str            # cobit | coso | rgsi
    code: str                 # "APO13.01"
    title: str
    domain: Optional[str] = None       # COBIT: dominio
    component: Optional[str] = None    # COSO: componente
    section: Optional[str] = None      # RGSI: sección
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)

    @classmethod
    def from_firestore(cls, doc_id: str, framework: str, data: dict) -> "FrameworkControl":
        return cls(
            id=doc_id,
            framework=framework,
            code=data.get("code", ""),
            title=data.get("title", ""),
            domain=data.get("domain"),
            component=data.get("component"),
            section=data.get("section"),
            description=data.get("description"),
            keywords=data.get("keywords", []),
        )
