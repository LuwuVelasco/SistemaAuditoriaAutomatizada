"""Excepciones personalizadas del dominio SAAM."""

from fastapi import HTTPException, status


class SAAMException(Exception):
    """Base para todas las excepciones del sistema."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(SAAMException):
    """Recurso no encontrado."""


class ForbiddenError(SAAMException):
    """Acceso denegado — no es el propietario."""


class ValidationError(SAAMException):
    """Error de validación de negocio."""


class AuthenticationError(SAAMException):
    """Token inválido o ausente."""


class StorageError(SAAMException):
    """Error al interactuar con Supabase Storage."""


class FirestoreError(SAAMException):
    """Error al interactuar con Firestore."""


class AIEngineError(SAAMException):
    """Error en uno de los motores Gemini."""


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def raise_not_found(resource: str, resource_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} '{resource_id}' no encontrado.",
    )


def raise_forbidden() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para acceder a este recurso.",
    )


def raise_unauthorized() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de autenticación inválido o ausente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
