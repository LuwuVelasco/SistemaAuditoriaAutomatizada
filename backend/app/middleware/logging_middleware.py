"""
Middleware de logging HTTP: registra cada request con método, path, status y duración.
"""

import time

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        method = request.method
        path   = request.url.path

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(f"{method} {path} → 500 | {type(exc).__name__}: {exc}")
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        status_code = response.status_code

        level = "warning" if status_code >= 400 else "info"
        getattr(logger, level)(
            f"{method} {path} → {status_code} | {elapsed_ms:.1f}ms"
        )
        return response
