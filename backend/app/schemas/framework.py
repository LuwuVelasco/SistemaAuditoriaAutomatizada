"""Schemas de salida para catálogos normativos."""

from typing import List, Optional

from pydantic import BaseModel


class FrameworkControlOut(BaseModel):
    id: str
    framework: str
    code: str
    title: str
    domain: Optional[str] = None
    component: Optional[str] = None
    section: Optional[str] = None
    description: Optional[str] = None
    keywords: List[str] = []
