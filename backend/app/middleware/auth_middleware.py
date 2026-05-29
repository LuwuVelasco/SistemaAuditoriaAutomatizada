"""
Middleware de autenticación: lista las rutas públicas que no requieren Bearer token.
La verificación real del token ocurre en deps.get_current_uid() para cada endpoint.
Este middleware solo bloquea rutas protegidas sin Authorization header presente,
devolviendo 401 temprano antes de entrar al router.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # IMPORTANTE:
        # Permitir requests preflight CORS
        if request.method == "OPTIONS":
            return await call_next(request)

        # Rutas públicas y prefijos docs
        if (
            path in _PUBLIC_PATHS
            or path.startswith("/docs")
            or path.startswith("/redoc")
        ):
            return await call_next(request)

        # Verificar presencia del header Authorization
        auth_header = request.headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Token de autenticación ausente.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)