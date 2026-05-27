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

    async def extract_from_documents(self, documents: List[Document]) -> Tuple[str, List[str]]:
        """
        Descarga y extrae texto e imágenes de todos los documentos.
        Retorna (texto_completo, lista_de_imagenes).
        """
        ready_docs = [d for d in documents if d.status.value == "ready"]
        if not ready_docs:
            logger.warning("ExtractionPipeline: sin documentos en estado 'ready'.")
            return "", []

        sections: List[str] = []
        all_images: List[str] = []

        for doc in ready_docs:
            logger.info(f"Extrayendo texto e imágenes de: {doc.name}")
            try:
                bucket = (
                    settings.SUPABASE_BUCKET_PDFS
                    if doc.type.lower() == "pdf"
                    else settings.SUPABASE_BUCKET_XLSX
                )
                content = await self._storage.download_file(bucket, doc.supabase_path)
                full_text, chunks, images = self._extractor.process(content, doc.name)
                
                if images:
                    all_images.extend(images)

                if full_text.strip():
                    sections.append(
                        f"=== DOCUMENTO: {doc.name} ===\n{full_text}"
                    )
                    logger.debug(f"{doc.name}: {len(chunks)} chunks extraídos, {len(images)} imágenes.")
                else:
                    logger.warning(f"{doc.name}: texto vacío tras extracción.")
            except Exception as exc:
                logger.error(f"Error al extraer {doc.name}: {exc}")

        combined = "\n\n".join(sections)
        logger.info(
            f"ExtractionPipeline: {len(ready_docs)} documentos -> {len(combined)} caracteres, {len(all_images)} imágenes totales."
        )
        return combined, all_images
