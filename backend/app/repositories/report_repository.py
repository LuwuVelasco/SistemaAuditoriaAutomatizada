"""Repositorio Firestore para reportes generados."""

from typing import List, Optional

from google.cloud import firestore
from loguru import logger

from app.models.report import Report
from app.utils.helpers import strip_none


class ReportRepository:
    def __init__(self, db: firestore.AsyncClient):
        self._db = db

    def _col(self, audit_id: str) -> firestore.AsyncCollectionReference:
        return self._db.collection("audits").document(audit_id).collection("reports")

    async def create(self, report: Report) -> Report:
        data = strip_none(report.to_firestore())
        await self._col(report.audit_id).document(report.id).set(data)
        logger.debug(f"Reporte registrado: {report.kind} -> {report.id}")
        return report

    async def list_by_audit(self, audit_id: str) -> List[Report]:
        docs = await self._col(audit_id).order_by("generatedAt", direction=firestore.Query.DESCENDING).get()
        return [Report.from_firestore(d.id, audit_id, d.to_dict()) for d in docs]

    async def get_by_id(self, audit_id: str, report_id: str) -> Optional[Report]:
        doc = await self._col(audit_id).document(report_id).get()
        if not doc.exists:
            return None
        return Report.from_firestore(doc.id, audit_id, doc.to_dict())

    async def delete(self, audit_id: str, report_id: str) -> None:
        await self._col(audit_id).document(report_id).delete()
