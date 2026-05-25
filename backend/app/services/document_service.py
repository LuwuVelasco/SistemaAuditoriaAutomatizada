"""Servicio para gestión de documentos cargados por auditoría."""

from typing import List

from loguru import logger

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.document import Document
from app.repositories.audit_repository import AuditRepository
from app.repositories.document_repository import DocumentRepository
from app.services.storage_service import StorageService
from app.utils.enums import DocumentStatus
from app.utils.helpers import generate_id
from app.utils.timestamps import utcnow_iso
from app.core.config import settings


class DocumentService:
    def __init__(
        self,
        doc_repo: DocumentRepository,
        audit_repo: AuditRepository,
        storage: StorageService,
    ):
        self._docs = doc_repo
        self._audits = audit_repo
        self._storage = storage

    async def _assert_owner(self, audit_id: str, owner_id: str) -> None:
        if not await self._audits.verify_owner(audit_id, owner_id):
            raise ForbiddenError("No tienes acceso a esta auditoría.")

    async def upload(
        self,
        audit_id: str,
        owner_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> Document:
        await self._assert_owner(audit_id, owner_id)

        file_size_mb = len(content) / (1024 * 1024)
        size_str = f"{file_size_mb:.1f} MB" if file_size_mb >= 1 else f"{len(content) // 1024} KB"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
        sha256 = StorageService.compute_sha256(content)

        supabase_path = await self._storage.upload_pdf(audit_id, filename, content)
        doc_id = generate_id("doc-")

        document = Document(
            id=doc_id,
            auditId=audit_id,
            name=filename,
            type=ext,
            size=size_str,
            supabasePath=supabase_path,
            status=DocumentStatus.QUEUED,
            chunks=0,
            sha256=sha256,
            uploadedAt=utcnow_iso(),
        )

        await self._docs.create(document)
        await self._audits.increment_counter(audit_id, "documentsCount", 1)

        logger.info(f"Documento subido: {filename} → {doc_id} (auditoría {audit_id})")
        return document

    async def list_by_audit(self, audit_id: str, owner_id: str) -> List[Document]:
        await self._assert_owner(audit_id, owner_id)
        return await self._docs.list_by_audit(audit_id)

    async def get_by_id(self, audit_id: str, doc_id: str, owner_id: str) -> Document:
        await self._assert_owner(audit_id, owner_id)
        doc = await self._docs.get_by_id(audit_id, doc_id)
        if doc is None:
            raise NotFoundError("Documento", doc_id)
        return doc

    async def delete(self, audit_id: str, doc_id: str, owner_id: str) -> None:
        doc = await self.get_by_id(audit_id, doc_id, owner_id)
        await self._storage.delete_file(settings.SUPABASE_BUCKET_PDFS, doc.supabase_path)
        await self._docs.delete(audit_id, doc_id)
        await self._audits.increment_counter(audit_id, "documentsCount", -1)
        logger.info(f"Documento eliminado: {doc_id}")

    async def download_content(self, audit_id: str, doc_id: str, owner_id: str) -> bytes:
        """Descarga el contenido binario de un documento desde Supabase."""
        doc = await self.get_by_id(audit_id, doc_id, owner_id)
        return await self._storage.download_file(settings.SUPABASE_BUCKET_PDFS, doc.supabase_path)

    async def update_status(
        self, audit_id: str, doc_id: str, status: DocumentStatus, chunks: int = 0
    ) -> None:
        """Actualización interna de estado (sin verificar owner — uso del pipeline)."""
        await self._docs.update_status(audit_id, doc_id, status.value, chunks)
