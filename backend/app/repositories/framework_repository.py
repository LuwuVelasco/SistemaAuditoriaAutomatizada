"""Repositorio Firestore para el catálogo normativo (read-only desde la API)."""

from typing import List, Optional

from google.cloud import firestore

from app.models.framework import FrameworkControl


class FrameworkRepository:
    def __init__(self, db: firestore.AsyncClient):
        self._db = db

    def _col(self, framework: str) -> firestore.AsyncCollectionReference:
        return (
            self._db.collection("frameworks")
            .document(framework.lower())
            .collection("controls")
        )

    async def list_controls(self, framework: str) -> List[FrameworkControl]:
        docs = await self._col(framework).order_by("code").get()
        return [FrameworkControl.from_firestore(d.id, framework.lower(), d.to_dict()) for d in docs]

    async def get_control(self, framework: str, control_id: str) -> Optional[FrameworkControl]:
        doc = await self._col(framework).document(control_id).get()
        if not doc.exists:
            return None
        return FrameworkControl.from_firestore(doc.id, framework.lower(), doc.to_dict())

    async def search_by_keyword(self, framework: str, keyword: str) -> List[FrameworkControl]:
        """Búsqueda simple por keyword en el array 'keywords'."""
        query = self._col(framework).where("keywords", "array_contains", keyword.lower())
        docs = await query.get()
        return [FrameworkControl.from_firestore(d.id, framework.lower(), d.to_dict()) for d in docs]
