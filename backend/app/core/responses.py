"""Respuestas HTTP uniformes para toda la API."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Respuesta estándar de la API."""

    success: bool
    message: str = ""
    data: T | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada estándar."""

    success: bool = True
    message: str = ""
    data: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


def ok(data: Any = None, message: str = "OK") -> dict:
    """Respuesta exitosa."""
    return {"success": True, "message": message, "data": data}


def created(data: Any = None, message: str = "Creado correctamente.") -> dict:
    """Respuesta de creación exitosa."""
    return {"success": True, "message": message, "data": data}


def error(message: str, details: dict | None = None) -> dict:
    """Respuesta de error."""
    return {"success": False, "message": message, "details": details or {}}
