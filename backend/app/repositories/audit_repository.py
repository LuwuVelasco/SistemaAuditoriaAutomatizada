"""Repositorio Firestore para auditorías."""

from typing import List, Optional

from google.cloud import firestore
from loguru import logger

from app.models.audit import Audit
from app.utils.helpers import strip_none


class AuditRepository:
    def __init__(self, db: firestore.AsyncClient):
        self._col = db.collection("audits")

    async def create(self, audit: Audit) -> Audit:
        data = strip_none(audit.to_firestore())
        await self._col.document(audit.id).set(data)
        logger.debug(f"Auditoría creada: {audit.id}")
        return audit

    async def get_by_id(self, audit_id: str) -> Optional[Audit]:
        doc = await self._col.document(audit_id).get()
        if not doc.exists:
            return None
        return Audit.from_firestore(doc.id, doc.to_dict())

    async def list_by_owner(self, owner_id: str) -> List[Audit]:
        query = (
            self._col
            .where("ownerId", "==", owner_id)
            .order_by("createdAt", direction=firestore.Query.DESCENDING)
        )
        docs = await query.get()
        return [Audit.from_firestore(d.id, d.to_dict()) for d in docs]

    async def update(self, audit_id: str, fields: dict) -> Optional[Audit]:
        """Actualiza solo los campos provistos (PATCH semántico)."""
        clean = strip_none(fields)
        if not clean:
            return await self.get_by_id(audit_id)
        await self._col.document(audit_id).update(clean)
        logger.debug(f"Auditoría actualizada: {audit_id} → {list(clean.keys())}")
        return await self.get_by_id(audit_id)

    async def delete(self, audit_id: str) -> None:
        await self._col.document(audit_id).delete()
        logger.debug(f"Auditoría eliminada: {audit_id}")

    async def verify_owner(self, audit_id: str, owner_id: str) -> bool:
        doc = await self._col.document(audit_id).get()
        if not doc.exists:
            return False
        return doc.to_dict().get("ownerId") == owner_id

    async def increment_counter(self, audit_id: str, field: str, delta: int = 1) -> None:
        await self._col.document(audit_id).update({field: firestore.Increment(delta)})
