"""
Aplicación FastAPI principal del backend SAAM.

Registra:
- Middleware (CORS, logging, auth)
- Routers versionados bajo /api/v1
- Manejadores de excepciones del dominio
- Health check
- Lifespan (init Firebase en startup)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.routes import audits, auth, chat, dashboard, documents, findings, frameworks, reports
from app.core.config import settings
from app.core.exceptions import (
    AIEngineError,
    AuthenticationError,
    ForbiddenError,
    FirestoreError,
    NotFoundError,
    SAAMException,
    StorageError,
    ValidationError,
)
from app.core.firebase import init_firebase
from app.core.logging import setup_logging
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.logging_middleware import LoggingMiddleware


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_firebase()
    logger.info(f"[SAAM] Backend iniciado — entorno: {settings.APP_ENV}")
    yield
    logger.info("[SAAM] Backend detenido.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SAAM — Sistema de Auditoría Automatizada Multimarco",
    description=(
        "API REST para COSFI/SAAM. Procesa auditorías TI con tres motores IA "
        "(COSO, COBIT, RGSI) y almacena hallazgos en Firestore."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middleware (orden importa: primero CORS, luego logging, luego auth) ───────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)


# ── Exception handlers ────────────────────────────────────────────────────────

def _err(status_code: int, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": message, "details": details or {}},
    )


@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError):
    return _err(status.HTTP_404_NOT_FOUND, exc.message)


@app.exception_handler(ForbiddenError)
async def handle_forbidden(request: Request, exc: ForbiddenError):
    return _err(status.HTTP_403_FORBIDDEN, exc.message)


@app.exception_handler(AuthenticationError)
async def handle_auth(request: Request, exc: AuthenticationError):
    return _err(status.HTTP_401_UNAUTHORIZED, exc.message)


@app.exception_handler(ValidationError)
async def handle_validation(request: Request, exc: ValidationError):
    return _err(status.HTTP_422_UNPROCESSABLE_ENTITY, exc.message, exc.details)


@app.exception_handler(StorageError)
async def handle_storage(request: Request, exc: StorageError):
    logger.error(f"StorageError: {exc.message}")
    return _err(status.HTTP_503_SERVICE_UNAVAILABLE, "Error de almacenamiento.", exc.details)


@app.exception_handler(FirestoreError)
async def handle_firestore(request: Request, exc: FirestoreError):
    logger.error(f"FirestoreError: {exc.message}")
    return _err(status.HTTP_503_SERVICE_UNAVAILABLE, "Error de base de datos.", exc.details)


@app.exception_handler(AIEngineError)
async def handle_ai(request: Request, exc: AIEngineError):
    logger.error(f"AIEngineError: {exc.message}")
    return _err(status.HTTP_502_BAD_GATEWAY, "Error en motor IA.", exc.details)


@app.exception_handler(SAAMException)
async def handle_saam(request: Request, exc: SAAMException):
    logger.error(f"SAAMException: {exc.message}")
    return _err(status.HTTP_500_INTERNAL_SERVER_ERROR, exc.message)


@app.exception_handler(Exception)
async def handle_generic(request: Request, exc: Exception):
    logger.exception(f"Error no controlado: {exc}")
    return _err(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error interno del servidor.")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/", tags=["health"])
async def root():
    return {"message": f"SAAM Backend v1.0.0 — {settings.APP_ENV}"}


# ── Routers ───────────────────────────────────────────────────────────────────

PREFIX = settings.API_V1_PREFIX

app.include_router(auth.router,       prefix=PREFIX)
app.include_router(audits.router,     prefix=PREFIX)
app.include_router(documents.router,  prefix=PREFIX)
app.include_router(findings.router,   prefix=PREFIX)
app.include_router(reports.router,    prefix=PREFIX)
app.include_router(chat.router,       prefix=PREFIX)
app.include_router(dashboard.router,  prefix=PREFIX)
app.include_router(frameworks.router, prefix=PREFIX)
