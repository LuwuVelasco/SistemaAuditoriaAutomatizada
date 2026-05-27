"""
Pipeline de extracción: descarga documentos de Supabase y extrae texto para los motores.
"""

from typing import List, Tuple

from loguru import logger

from app.core.config import settings
from app.models.document import Document
from app.services.extraction_service import ExtractionService
from app.services.storage_service import StorageService


class ExtractionPipeline:
    """
    Orquesta la descarga de documentos desde Supabase Storage
    y la extracción de texto para el pipeline IA.
    """

    def __init__(self, storage: StorageService, extractor: ExtractionService):
        self._storage = storage
        self._extractor = extractor

    async def extract_from_documents(self, documents: List[Document]) -> str:
        """
        Descarga y extrae texto de todos los documentos.
        Concatena el contenido con separadores de sección.
        Retorna el texto completo listo para el análisis IA.
        """
        ready_docs = [d for d in documents if d.status.value == "ready"]
        if not ready_docs:
            logger.warning("ExtractionPipeline: sin documentos en estado 'ready'.")
            return ""

        sections: List[str] = []

        for doc in ready_docs:
            logger.info(f"Extrayendo texto de: {doc.name}")
            try:
                bucket = (
                    settings.SUPABASE_BUCKET_PDFS
                    if doc.type.lower() == "pdf"
                    else settings.SUPABASE_BUCKET_XLSX
                )
                content = await self._storage.download_file(bucket, doc.supabase_path)
                full_text, chunks = self._extractor.process(content, doc.name)
                if full_text.strip():
                    sections.append(
                        f"=== DOCUMENTO: {doc.name} ===\n{full_text}"
                    )
                    logger.debug(f"{doc.name}: {len(chunks)} chunks extraídos.")
                else:
                    logger.warning(f"{doc.name}: texto vacío tras extracción.")
            except Exception as exc:
                logger.error(f"Error al extraer {doc.name}: {exc}")

        combined = "\n\n".join(sections)
        logger.info(
            f"ExtractionPipeline: {len(ready_docs)} documentos -> {len(combined)} caracteres totales."
        )
        return combined
