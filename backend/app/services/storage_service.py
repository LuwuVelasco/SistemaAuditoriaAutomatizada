"""Servicio de almacenamiento de binarios en Supabase Storage."""

import hashlib
import io
from typing import Optional
from urllib.parse import quote

import httpx
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
            logger.debug(f"Iniciando upload PDF: bucket={bucket}, path={path}, size={len(content)} bytes")
            result = self._client.storage.from_(bucket).upload(
                path=path,
                file=content,
                file_options={"content-type": "application/pdf", "upsert": "true"},
            )
            logger.info(f"PDF subido exitosamente → {bucket}/{path} | respuesta: {result}")
            return path
        except Exception as exc:
            msg = str(exc)
            if "row-level security policy" in msg:
                raise StorageError(
                    "Error al subir PDF a Supabase: RLS bloqueó la operación. "
                    "Configura policies para storage.objects o usa SUPABASE_KEY de backend (service_role)."
                ) from exc
            raise StorageError(f"Error al subir PDF a Supabase: {exc}") from exc

    async def download_file(self, bucket: str, path: str) -> bytes:
        """Descarga el contenido binario de un archivo de Supabase Storage.

        Usamos URL firmada + HTTP para evitar fallos intermitentes del endpoint
        de descarga directa del SDK en algunos entornos.
        URL-encodifica el path para manejar correctamente espacios y caracteres especiales.
        """
        try:
            # URL-encodifica el path: "5. PESI Banco.pdf" → "5%2E%20PESI%20Banco.pdf"
            encoded_path = quote(path, safe="/")
            signed = self._client.storage.from_(bucket).create_signed_url(encoded_path, 120, {"download": True})
            signed_url = signed.get("signedURL") or signed.get("signedUrl")
            if not signed_url:
                raise StorageError(f"No se pudo generar URL firmada para '{bucket}/{path}'.")

            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(signed_url)
                response.raise_for_status()
                return response.content
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
            logger.info(f"Reporte subido → {bucket}/{path}")
            return path
        except Exception as exc:
            msg = str(exc)
            if "row-level security policy" in msg:
                raise StorageError(
                    "Error al subir reporte a Supabase: RLS bloqueó la operación. "
                    "Configura policies para storage.objects o usa SUPABASE_KEY de backend (service_role)."
                ) from exc
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
