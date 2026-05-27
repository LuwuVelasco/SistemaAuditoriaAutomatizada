"""
Servicio IA: conecta el orquestador con los repositorios.
Responsable del flujo completo desde la petición HTTP hasta el almacenamiento de hallazgos.
"""

from loguru import logger

from app.ai.cobit_engine import COBITEngine
from app.ai.coso_engine import COSOEngine
from app.ai.extraction_pipeline import ExtractionPipeline
from app.ai.finding_merger import FindingMerger
from app.ai.orchestrator import AIOrchestrator
from app.ai.rgsi_engine import RGSIEngine
from app.core.exceptions import NotFoundError
from app.repositories.audit_repository import AuditRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.finding_repository import FindingRepository
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.extraction_service import ExtractionService
from app.services.finding_service import FindingService
from app.services.storage_service import StorageService
from app.utils.enums import AuditStatus, DocumentStatus


class AIService:
    """
    Orquesta el pipeline IA completo:
    documentos → extracción → motores → consolidación → hallazgos en Firestore
    """

    def __init__(
        self,
        audit_repo: AuditRepository,
        doc_repo: DocumentRepository,
        finding_service: FindingService,
        storage: StorageService,
        audit_service: AuditService,
        doc_service: DocumentService,
    ):
        self._audit_repo = audit_repo
        self._doc_repo = doc_repo
        self._finding_service = finding_service
        self._storage = storage
        self._audit_service = audit_service
        self._doc_service = doc_service

    async def run_analysis(self, audit_id: str) -> int:
        """
        Ejecuta el pipeline IA completo para una auditoría.
        Retorna el número de hallazgos generados.
        Se llama desde un BackgroundTask — no bloquea el request HTTP.
        """
        logger.info(f"[AIService] Iniciando pipeline para auditoría {audit_id}")
        findings = []
        ready_docs = []
        should_finalize = False

        try:
            # ── Cargar auditoría ──────────────────────────────────────────────────
            audit = await self._audit_repo.get_by_id(audit_id)
            if not audit:
                raise NotFoundError("Auditoría", audit_id)

            await self._audit_service.set_status(audit_id, AuditStatus.PROCESANDO, 5)

            # ── Cargar documentos listos ──────────────────────────────────────────
            all_docs = await self._doc_repo.list_by_audit(audit_id)
            ready_docs = [d for d in all_docs if d.status == DocumentStatus.READY]

            if not ready_docs:
                logger.warning(f"[AIService] Sin documentos 'ready' en auditoría {audit_id}.")
                await self._audit_service.set_status(audit_id, AuditStatus.PENDIENTE, 0)
                return 0

            # Actualizar docs a 'indexing'
            for doc in ready_docs:
                await self._doc_service.update_status(audit_id, doc.id, DocumentStatus.INDEXING)

            should_finalize = True
            await self._audit_service.set_status(audit_id, AuditStatus.PROCESANDO, 20)

            # ── Construir y ejecutar orquestador ─────────────────────────────────
            extractor = ExtractionService()
            extraction_pipeline = ExtractionPipeline(self._storage, extractor)

            orchestrator = AIOrchestrator(
                extraction_pipeline=extraction_pipeline,
                coso_engine=COSOEngine(),
                cobit_engine=COBITEngine(),
                rgsi_engine=RGSIEngine(),
                merger=FindingMerger(),
            )

            await self._audit_service.set_status(audit_id, AuditStatus.PROCESANDO, 40)

            findings = await orchestrator.run(
                audit_id=audit_id,
                frameworks=audit.frameworks,
                documents=ready_docs,
            )

            await self._audit_service.set_status(audit_id, AuditStatus.PROCESANDO, 80)

            # ── Persistir hallazgos ───────────────────────────────────────────────
            if findings:
                await self._finding_service.create_batch_internal(audit_id, findings)

            logger.info(f"[AIService] Pipeline completado: {len(findings)} hallazgos en {audit_id}.")
            return len(findings)

        except Exception as exc:
            logger.exception(f"[AIService] Error no controlado durante el pipeline de {audit_id}: {exc}")
            return len(findings)
        finally:
            # Siempre devolver los documentos a ready para no bloquear nuevas corridas.
            if should_finalize:
                for doc in ready_docs:
                    try:
                        await self._doc_service.update_status(
                            audit_id, doc.id, DocumentStatus.READY, chunks=50
                        )
                    except Exception as exc:
                        logger.warning(f"[AIService] No se pudo restaurar el documento {doc.id} a ready: {exc}")

                try:
                    await self._audit_service.set_status(audit_id, AuditStatus.EN_REVISION, 100)
                except Exception as exc:
                    logger.warning(f"[AIService] No se pudo actualizar el estado final de auditoría {audit_id}: {exc}")
