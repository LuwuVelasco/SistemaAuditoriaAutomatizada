"""Servicio de historial de cambios en hallazgos (trazabilidad regulatoria)."""

from typing import Any, List

from google.cloud import firestore
from loguru import logger

from app.utils.helpers import generate_id
from app.utils.timestamps import utcnow_iso

# Campos que disparan un evento de historia
TRACKED_FIELDS = {"status", "impact", "probability", "recommendation", "risk"}


class HistoryService:
    def __init__(self, db: firestore.AsyncClient):
        self._db = db

    def _history_col(self, audit_id: str, finding_id: str):
        return (
            self._db.collection("audits")
            .document(audit_id)
            .collection("findings")
            .document(finding_id)
            .collection("history")
        )

    async def record_change(
        self,
        audit_id: str,
        finding_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        changed_by: str,
    ) -> None:
        """Escribe un evento inmutable en history/{eventId}."""
        if old_value == new_value:
            return  # Sin cambio real — no registrar

        event_id = generate_id("evt-")
        event = {
            "field": field,
            "oldValue": old_value,
            "newValue": new_value,
            "changedBy": changed_by,
            "changedAt": utcnow_iso(),
        }
        await self._history_col(audit_id, finding_id).document(event_id).set(event)
        logger.debug(f"Historia [{finding_id}] campo '{field}': {old_value!r} → {new_value!r}")

    async def record_update(
        self,
        audit_id: str,
        finding_id: str,
        old_data: dict,
        new_data: dict,
        changed_by: str,
    ) -> None:
        """Compara old_data vs new_data y registra los campos modificados."""
        for field in TRACKED_FIELDS:
            old_val = old_data.get(field)
            new_val = new_data.get(field)
            if new_val is not None and old_val != new_val:
                await self.record_change(
                    audit_id, finding_id, field, old_val, new_val, changed_by
                )

    async def get_history(self, audit_id: str, finding_id: str) -> List[dict]:
        """Devuelve el historial completo de un hallazgo, ordenado cronológicamente."""
        docs = await self._history_col(audit_id, finding_id).order_by("changedAt").get()
        return [{"id": d.id, **d.to_dict()} for d in docs]
