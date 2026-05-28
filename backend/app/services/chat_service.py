"""
Servicio de chat con documentos de auditoría.
Extrae texto de los documentos subidos y responde preguntas usando Gemini.
"""

from loguru import logger

from app.ai.extraction_pipeline import ExtractionPipeline
from app.ai.providers.gemini_provider import GeminiProvider
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repositories.audit_repository import AuditRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.chat import ChatMessage
from app.services.extraction_service import ExtractionService
from app.services.storage_service import StorageService
from app.utils.enums import DocumentStatus

_MAX_CONTEXT_CHARS = 60_000


class ChatService:
    def __init__(
        self,
        audit_repo: AuditRepository,
        doc_repo: DocumentRepository,
        storage: StorageService,
        provider: GeminiProvider,
    ):
        self._audits = audit_repo
        self._docs = doc_repo
        self._storage = storage
        self._provider = provider

    async def chat(
        self,
        audit_id: str,
        owner_id: str,
        question: str,
        history: list[ChatMessage],
    ) -> str:
        audit = await self._audits.get_by_id(audit_id)
        if not audit:
            raise NotFoundError("Auditoría", audit_id)
        if audit.owner_id != owner_id:
            raise ForbiddenError("No tienes acceso a esta auditoría.")

        # Extraer texto de los documentos listos
        all_docs = await self._docs.list_by_audit(audit_id)
        ready_docs = [d for d in all_docs if d.status == DocumentStatus.READY]

        context = ""
        if ready_docs:
            try:
                pipeline = ExtractionPipeline(self._storage, ExtractionService())
                raw_text = await pipeline.extract_from_documents(ready_docs)
                if len(raw_text) > _MAX_CONTEXT_CHARS:
                    raw_text = raw_text[:_MAX_CONTEXT_CHARS] + "\n[... contenido truncado ...]"
                context = raw_text
            except Exception as exc:
                logger.warning(f"[ChatService] No se pudo extraer texto: {exc}")

        prompt = self._build_prompt(audit, context, question, history)
        logger.info(f"[ChatService] Consulta para auditoría {audit_id}: {question[:80]}")

        answer = await self._provider.generate(prompt, temperature=0.4, json_mode=False)
        return answer.strip()

    def _build_prompt(self, audit, context: str, question: str, history: list[ChatMessage]) -> str:
        doc_section = (
            f"A continuación está el contenido extraído de los documentos de la auditoría:\n\n{context}"
            if context
            else "No hay documentos cargados en esta auditoría aún."
        )

        history_section = ""
        if history:
            lines = []
            for msg in history[-10:]:  # últimos 10 turnos para no saturar el prompt
                label = "Usuario" if msg.role == "user" else "Asistente"
                lines.append(f"{label}: {msg.content}")
            history_section = "\n\nHistorial de conversación:\n" + "\n".join(lines)

        return f"""Eres un asistente experto en auditoría de tecnología de la información para la empresa "{audit.entity}".
Tu función es responder preguntas sobre los documentos de auditoría del período {audit.period}.
Responde siempre en español, de forma clara y concisa.
Si la pregunta no puede responderse con la información disponible, dilo honestamente.

{doc_section}
{history_section}

Pregunta del auditor: {question}

Respuesta:"""
