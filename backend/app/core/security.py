"""Verificación de tokens Firebase JWT."""

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import raise_unauthorized
from app.core.firebase import verify_token

bearer_scheme = HTTPBearer(auto_error=False)


def extract_uid_from_request(request: Request) -> str:
    """
    Extrae el UID del Bearer token Firebase en el header Authorization.
    Lanza HTTP 401 si el token es inválido o está ausente.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise_unauthorized()

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise_unauthorized()

    try:
        payload = verify_token(token)
        return payload["uid"]
    except (ValueError, KeyError):
        raise_unauthorized()
