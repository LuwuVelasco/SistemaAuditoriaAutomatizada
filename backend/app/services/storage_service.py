"""Servicio de almacenamiento de binarios en Supabase Storage."""

import hashlib
import io
from typing import Optional

from loguru import logger
from supabase import Client

from app.core.config import settings
from app.core.exceptions import StorageError


class StorageService:
    def __init__(self, supabase: Client):
        self._client = supabase

    # ── PDF upload ─────────────────────────────────────────────────────────

    async def upload_pdf(self, audit_id: str, filename: str, content: bytes) -> str:
        """
        Sube un PDF a Supabase Storage.
        Retorna la ruta de almacenamiento: 'pdfs/audits/{auditId}/{filename}'
        """
        path = f"audits/{audit_id}/{filename}"
        bucket = settings.SUPABASE_BUCKET_PDFS
        try:
            self._client.storage.from_(bucket).upload(
                path=path,
                file=content,
                file_options={"content-type": "application/pdf", "upsert": "true"},
            )
            logger.info(f"PDF subido -> {bucket}/{path}")
            return path
        except Exception as exc:
            raise StorageError(f"Error al subir PDF a Supabase: {exc}") from exc

    async def download_file(self, bucket: str, path: str) -> bytes:
        """Descarga el contenido binario de un archivo de Supabase Storage."""
        try:
            response = self._client.storage.from_(bucket).download(path)
            return response
        except Exception as exc:
            raise StorageError(f"Error al descargar '{path}' desde Supabase: {exc}") from exc

    async def upload_report(self, audit_id: str, filename: str, content: bytes, content_type: str) -> str:
        """Sube un reporte (XLSX/DOCX/PDF) al bucket de reportes."""
        path = f"audits/{audit_id}/{filename}"
        bucket = settings.SUPABASE_BUCKET_XLSX
        try:
            self._client.storage.from_(bucket).upload(
                path=path,
                file=content,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            logger.info(f"Reporte subido -> {bucket}/{path}")
            return path
        except Exception as exc:
            raise StorageError(f"Error al subir reporte a Supabase: {exc}") from exc

    async def delete_file(self, bucket: str, path: str) -> None:
        """Elimina un archivo de Supabase Storage."""
        try:
            self._client.storage.from_(bucket).remove([path])
            logger.debug(f"Archivo eliminado: {bucket}/{path}")
        except Exception as exc:
            logger.warning(f"No se pudo eliminar {bucket}/{path}: {exc}")

    def get_public_url(self, bucket: str, path: str) -> str:
        """Genera URL pública (si el bucket es público) o firmada."""
        try:
            data = self._client.storage.from_(bucket).get_public_url(path)
            return data
        except Exception:
            return ""

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
