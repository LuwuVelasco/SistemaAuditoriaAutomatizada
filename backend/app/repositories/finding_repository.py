"""Repositorio Firestore para hallazgos (subcolección de auditorías)."""

from typing import List, Optional

from google.cloud import firestore
from loguru import logger

from app.models.finding import Finding
from app.utils.helpers import strip_none


class FindingRepository:
    def __init__(self, db: firestore.AsyncClient):
        self._db = db

    def _col(self, audit_id: str) -> firestore.AsyncCollectionReference:
        return self._db.collection("audits").document(audit_id).collection("findings")

    async def create(self, finding: Finding) -> Finding:
        data = strip_none(finding.to_firestore())
        await self._col(finding.audit_id).document(finding.id).set(data)
        logger.debug(f"Hallazgo creado: {finding.id} en auditoría {finding.audit_id}")
        return finding

    async def create_batch(self, findings: List[Finding]) -> List[Finding]:
        """Inserta múltiples hallazgos en un solo batch write."""
        if not findings:
            return []
        batch = self._db.batch()
        for f in findings:
            ref = self._col(f.audit_id).document(f.id)
            batch.set(ref, strip_none(f.to_firestore()))
        await batch.commit()
        logger.info(f"Batch de {len(findings)} hallazgos creados.")
        return findings

    async def get_by_id(self, audit_id: str, finding_id: str) -> Optional[Finding]:
        doc = await self._col(audit_id).document(finding_id).get()
        if not doc.exists:
            return None
        return Finding.from_firestore(doc.id, audit_id, doc.to_dict())

    async def list_by_audit(self, audit_id: str) -> List[Finding]:
        docs = await self._col(audit_id).order_by("createdAt").get()
        return [Finding.from_firestore(d.id, audit_id, d.to_dict()) for d in docs]

    async def list_by_status(self, audit_id: str, status: str) -> List[Finding]:
        query = self._col(audit_id).where("status", "==", status)
        docs = await query.get()
        return [Finding.from_firestore(d.id, audit_id, d.to_dict()) for d in docs]

    async def update(self, audit_id: str, finding_id: str, fields: dict) -> Optional[Finding]:
        clean = {k: v for k, v in fields.items() if v is not None}
        if not clean:
            return await self.get_by_id(audit_id, finding_id)
        await self._col(audit_id).document(finding_id).update(clean)
        logger.debug(f"Hallazgo actualizado: {finding_id} → campos: {list(clean.keys())}")
        return await self.get_by_id(audit_id, finding_id)

    async def delete(self, audit_id: str, finding_id: str) -> None:
        await self._col(audit_id).document(finding_id).delete()
        logger.debug(f"Hallazgo eliminado: {finding_id}")

    async def count_by_status(self, audit_id: str) -> dict:
        """Contadores por estado para KPIs de dashboard."""
        docs = await self._col(audit_id).get()
        counts: dict = {}
        for d in docs:
            status = d.to_dict().get("status", "Pendiente")
            counts[status] = counts.get(status, 0) + 1
        return counts

    async def count_by_risk(self, audit_id: str) -> dict:
        docs = await self._col(audit_id).get()
        counts: dict = {}
        for d in docs:
            risk = d.to_dict().get("risk", "Medio")
            counts[risk] = counts.get(risk, 0) + 1
        return counts
