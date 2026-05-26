"""Repositorio Firestore para documentos (subcolección de auditorías)."""

from typing import List, Optional

from google.cloud import firestore
from loguru import logger

from app.models.document import Document
from app.utils.helpers import strip_none


class DocumentRepository:
    def __init__(self, db: firestore.AsyncClient):
        self._db = db

    def _col(self, audit_id: str) -> firestore.AsyncCollectionReference:
        return self._db.collection("audits").document(audit_id).collection("documents")

    async def create(self, document: Document) -> Document:
        data = strip_none(document.to_firestore())
        await self._col(document.audit_id).document(document.id).set(data)
        logger.debug(f"Documento registrado: {document.name} -> {document.id}")
        return document

    async def get_by_id(self, audit_id: str, doc_id: str) -> Optional[Document]:
        doc = await self._col(audit_id).document(doc_id).get()
        if not doc.exists:
            return None
        return Document.from_firestore(doc.id, audit_id, doc.to_dict())

    async def list_by_audit(self, audit_id: str) -> List[Document]:
        docs = await self._col(audit_id).order_by("uploadedAt").get()
        return [Document.from_firestore(d.id, audit_id, d.to_dict()) for d in docs]

    async def update_status(self, audit_id: str, doc_id: str, status: str, chunks: int = 0) -> None:
        update: dict = {"status": status}
        if chunks:
            update["chunks"] = chunks
        await self._col(audit_id).document(doc_id).update(update)
        logger.debug(f"Documento {doc_id} -> estado: {status}")

    async def delete(self, audit_id: str, doc_id: str) -> None:
        await self._col(audit_id).document(doc_id).delete()
        logger.debug(f"Documento eliminado: {doc_id}")
