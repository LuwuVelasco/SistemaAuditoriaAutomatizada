"""
Dependencias FastAPI compartidas por todos los routers.
Inyectan: usuario autenticado, clientes DB/Storage, y servicios de dominio.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.cloud import firestore

from app.core.firebase import get_firestore_client, verify_token
from app.core.exceptions import raise_unauthorized
from app.core.supabase import get_supabase_client
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.framework_repository import FrameworkRepository
from app.repositories.report_repository import ReportRepository
from app.services.ai_service import AIService
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.extraction_service import ExtractionService
from app.services.finding_service import FindingService
from app.services.framework_service import FrameworkService
from app.services.history_service import HistoryService
from app.services.report_service import ReportService
from app.services.storage_service import StorageService


# ── Infraestructura ───────────────────────────────────────────────────────────

def get_db() -> firestore.AsyncClient:
    return get_firestore_client()


def get_storage() -> StorageService:
    return StorageService(get_supabase_client())


# ── Repositorios ─────────────────────────────────────────────────────────────

def get_audit_repo(db: firestore.AsyncClient = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


def get_finding_repo(db: firestore.AsyncClient = Depends(get_db)) -> FindingRepository:
    return FindingRepository(db)


def get_document_repo(db: firestore.AsyncClient = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


def get_report_repo(db: firestore.AsyncClient = Depends(get_db)) -> ReportRepository:
    return ReportRepository(db)


def get_framework_repo(db: firestore.AsyncClient = Depends(get_db)) -> FrameworkRepository:
    return FrameworkRepository(db)


# ── Servicios ─────────────────────────────────────────────────────────────────

def get_history_service(db: firestore.AsyncClient = Depends(get_db)) -> HistoryService:
    return HistoryService(db)


def get_audit_service(repo: AuditRepository = Depends(get_audit_repo)) -> AuditService:
    return AuditService(repo)


def get_finding_service(
    finding_repo: FindingRepository = Depends(get_finding_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    history: HistoryService = Depends(get_history_service),
) -> FindingService:
    return FindingService(finding_repo, audit_repo, history)


def get_document_service(
    doc_repo: DocumentRepository = Depends(get_document_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    storage: StorageService = Depends(get_storage),
) -> DocumentService:
    return DocumentService(doc_repo, audit_repo, storage)


def get_report_service(
    audit_repo: AuditRepository = Depends(get_audit_repo),
    finding_repo: FindingRepository = Depends(get_finding_repo),
    report_repo: ReportRepository = Depends(get_report_repo),
    storage: StorageService = Depends(get_storage),
) -> ReportService:
    return ReportService(audit_repo, finding_repo, report_repo, storage)


def get_framework_service(repo: FrameworkRepository = Depends(get_framework_repo)) -> FrameworkService:
    return FrameworkService(repo)


def get_ai_service(
    audit_repo: AuditRepository = Depends(get_audit_repo),
    doc_repo: DocumentRepository = Depends(get_document_repo),
    finding_service: FindingService = Depends(get_finding_service),
    storage: StorageService = Depends(get_storage),
    audit_service: AuditService = Depends(get_audit_service),
    doc_service: DocumentService = Depends(get_document_service),
) -> AIService:
    return AIService(
        audit_repo=audit_repo,
        doc_repo=doc_repo,
        finding_service=finding_service,
        storage=storage,
        audit_service=audit_service,
        doc_service=doc_service,
    )


# ── Autenticación ─────────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


async def get_current_uid(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> str:
    """Extrae y verifica el Bearer token de Firebase. Retorna el UID."""
    if not credentials:
        raise_unauthorized()
    try:
        decoded = verify_token(credentials.credentials)
        return decoded["uid"]
    except Exception:
        raise_unauthorized()


async def get_current_user(
    uid: str = Depends(get_current_uid),
    db: firestore.AsyncClient = Depends(get_db),
) -> User:
    """Retorna el modelo User completo desde Firestore."""
    doc = await db.collection("users").document(uid).get()
    if not doc.exists:
        # Usuario autenticado pero sin perfil aún — crear básico
        return User(
            id=uid,
            email="",
            displayName="",
            role="auditor",
            createdAt="",
        )
    return User.from_firestore(doc.id, doc.to_dict())


# ── Type aliases para inyección limpia ────────────────────────────────────────

CurrentUID  = Annotated[str, Depends(get_current_uid)]
CurrentUser = Annotated[User, Depends(get_current_user)]
DB          = Annotated[firestore.AsyncClient, Depends(get_db)]
