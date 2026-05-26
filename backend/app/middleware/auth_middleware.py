"""
Middleware de autenticación early-exit.
En DEBUG=True se omite: la validación real ocurre en get_current_uid() por endpoint.
En producción bloquea rutas protegidas sin Authorization header antes del router.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

_PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # En desarrollo el dep get_current_uid() maneja la auth por endpoint
        if settings.DEBUG:
            return await call_next(request)

        path = request.url.path

        if path in _PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Token de autenticación ausente."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
