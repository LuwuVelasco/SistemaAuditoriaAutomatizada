"""Schemas compartidos por toda la API."""

from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str = ""
    data: T | None = None


class PaginatedAPIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = ""
    data: List[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


class HistoryEventOut(BaseModel):
    id: str
    field: str
    old_value: Any
    new_value: Any
    changed_by: str
    changed_at: str
