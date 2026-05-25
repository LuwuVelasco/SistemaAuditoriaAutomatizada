"""Parámetros y helpers de paginación."""

from typing import TypeVar

from fastapi import Query

T = TypeVar("T")


class PaginationParams:
    """Dependencia FastAPI para paginación estándar."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Página (empieza en 1)"),
        page_size: int = Query(default=20, ge=1, le=100, description="Elementos por página"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginate(items: list[T], params: PaginationParams) -> dict:
    """Aplica paginación en memoria a una lista."""
    total = len(items)
    start = params.offset
    end = start + params.page_size
    return {
        "data": items[start:end],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
    }
