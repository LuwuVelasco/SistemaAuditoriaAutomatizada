"""
Orquestador del pipeline IA multimarco.

Secuencia FIJA (según RGSI-ASFI, las regulaciones locales tienen precedencia):
  1. COBIT — analiza primero
  2. COSO  — recibe hallazgos COBIT como contexto
  3. RGSI  — recibe hallazgos COBIT + COSO como contexto

Solo se ejecutan los motores cuyo framework fue seleccionado en la auditoría.
Al finalizar, el FindingMerger consolida y deduplica todos los hallazgos.
"""

from typing import List, Optional

from loguru import logger

from app.ai.cobit_engine import COBITEngine
from app.ai.coso_engine import COSOEngine
from app.ai.extraction_pipeline import ExtractionPipeline
from app.ai.finding_merger import FindingMerger
from app.ai.rgsi_engine import RGSIEngine
from app.models.document import Document
from app.models.finding import Evidence, Finding, NormativeRef
from app.schemas.ai import RawFinding
from app.utils.enums import FindingStatus, FrameworkType, RiskLevel
from app.utils.helpers import generate_id
from app.utils.risk_matrix import calculate_risk
from app.utils.timestamps import utcnow_iso


class AIOrchestrator:
    """
    Coordina la ejecución secuencial de los motores IA y la consolidación
    de hallazgos para una auditoría específica.
    """

    def __init__(
        self,
        extraction_pipeline: ExtractionPipeline,
        coso_engine: COSOEngine,
        cobit_engine: COBITEngine,
        rgsi_engine: RGSIEngine,
        merger: FindingMerger,
    ):
        self._extraction = extraction_pipeline
        self._coso = coso_engine
        self._cobit = cobit_engine
        self._rgsi = rgsi_engine
        self._merger = merger

    async def run(
        self,
        audit_id: str,
        frameworks: List[FrameworkType],
        documents: List[Document],
        audit_meta: dict = None,
    ) -> List[Finding]:
        """
        Ejecuta el pipeline completo y retorna hallazgos listos para Firestore.

        Args:
            audit_id:   ID de la auditoría en Firestore.
            frameworks: Lista de frameworks seleccionados en la auditoría.
            documents:  Documentos con estado 'ready' asociados a la auditoría.
        """
        logger.info(
            f"[Orquestador] Iniciando análisis para auditoría {audit_id}. "
            f"Frameworks: {[f.value for f in frameworks]}"
        )

        # ── 1. Extracción de texto ────────────────────────────────────────────
        text = await self._extraction.extract_from_documents(documents)
        if not text:
            logger.error(f"[Orquestador] Sin texto extraíble en {audit_id}.")
            return []

        # ── 2. Ejecución secuencial de motores ───────────────────────────────
        all_raw: List[RawFinding] = []
        prior_dicts: List[dict] = []  # contexto acumulado para cada motor

        framework_values = {f.value for f in frameworks}

        # Motor 1: COBIT
        if "COBIT" in framework_values:
            cobit_results = await self._safe_analyze_motor(
                name="COBIT",
                engine=self._cobit,
                text=text,
                prior_findings=prior_dicts,
                audit_meta=audit_meta,
            )
            all_raw.extend(cobit_results)
            prior_dicts.extend([r.model_dump() for r in cobit_results])

        # Motor 2: COSO (recibe contexto COBIT si fue ejecutado)
        if "COSO" in framework_values:
            coso_results = await self._safe_analyze_motor(
                name="COSO",
                engine=self._coso,
                text=text,
                prior_findings=prior_dicts,
                audit_meta=audit_meta,
            )
            all_raw.extend(coso_results)
            prior_dicts.extend([r.model_dump() for r in coso_results])

        # Motor 3: RGSI (recibe contexto COBIT + COSO)
        if "RGSI" in framework_values:
            rgsi_results = await self._safe_analyze_motor(
                name="RGSI",
                engine=self._rgsi,
                text=text,
                prior_findings=prior_dicts,
                audit_meta=audit_meta,
            )
            all_raw.extend(rgsi_results)

        # ── 3. Consolidación y deduplicación ─────────────────────────────────
        try:
            consolidated = self._merger.merge(all_raw)
        except Exception as exc:
            logger.exception(
                f"[Orquestador] Error consolidando hallazgos en {audit_id}: {exc}. "
                "Se usarán los hallazgos crudos disponibles."
            )
            consolidated = all_raw

        # ── 4. Convertir a Finding del dominio ───────────────────────────────
        findings = [
            self._raw_to_finding(audit_id, raw, documents)
            for raw in consolidated
        ]

        logger.info(
            f"[Orquestador] Pipeline completado: {len(all_raw)} crudos → "
            f"{len(findings)} hallazgos finales para auditoría {audit_id}."
        )
        return findings

    async def _safe_analyze_motor(
        self,
        name: str,
        engine,
        text: str,
        prior_findings: List[dict],
        audit_meta: dict = None,
    ) -> List[RawFinding]:
        """
        Ejecuta un motor sin cortar el pipeline completo si falla.
        Devuelve [] cuando el motor no puede completarse.
        """
        try:
            results = await engine.analyze(text, prior_findings=prior_findings, audit_meta=audit_meta)
            logger.info(f"[{name}] {len(results)} hallazgos.")
            return results
        except Exception as exc:
            logger.exception(
                f"[Orquestador] Motor {name} falló y se omite para continuar el pipeline: {exc}"
            )
            return []

    def _raw_to_finding(self, audit_id: str, raw: RawFinding, documents: List[Document]) -> Finding:
        """Convierte un RawFinding (salida del motor) a Finding (modelo de dominio)."""
        now = utcnow_iso()
        finding_id = generate_id("HLZ-")

        # Usar impact=4 / probability=3 como valores iniciales para riesgo "Alto"
        # El auditor los ajustará en la UI.
        RISK_TO_IMPACT = {"Bajo": 2, "Medio": 3, "Alto": 4, "Extremo": 5}
        risk_source = raw.risk_level or "Medio"
        impact = RISK_TO_IMPACT.get(risk_source, 3)
        probability = RISK_TO_IMPACT.get(risk_source, 3) - 1 or 1
        risk = calculate_risk(impact, probability)

        def parse_refs(raw_list: List[dict]) -> List[NormativeRef]:
            result = []
            for r in raw_list:
                try:
                    result.append(NormativeRef(**r))
                except Exception:
                    pass
            return result

        def parse_evidence(raw_list: List[dict]) -> List[Evidence]:
            result: List[Evidence] = []
            seen = set()

            for item in raw_list or []:
                try:
                    evidence = Evidence.model_validate(item)
                except Exception:
                    continue

                key = (
                    evidence.doc_id,
                    evidence.doc_name,
                    evidence.page,
                    evidence.paragraph,
                )
                if key in seen:
                    continue
                seen.add(key)
                result.append(evidence)

            # Si Gemini no devolvió evidencias, persistir la relación con los
            # documentos analizados para que el hallazgo no quede huérfano.
            if not result:
                for doc in documents:
                    evidence = Evidence(docId=doc.id, docName=doc.name)
                    key = (evidence.doc_id, evidence.doc_name, evidence.page, evidence.paragraph)
                    if key in seen:
                        continue
                    seen.add(key)
                    result.append(evidence)

            return result

        return Finding(
            id=finding_id,
            auditId=audit_id,
            title=raw.title,
            description_finding=raw.description_finding or raw.conclusion,
            criteria_description=raw.criteria_description,
            cause=raw.cause,
            effect=raw.effect,
            conclusion=raw.conclusion,
            description=raw.description_finding or raw.conclusion,
            recommendation=raw.recommendation,
            risk=risk,
            risk_level=risk.value,
            impact=impact,
            probability=probability,
            status=FindingStatus.PENDIENTE,
            confidence=raw.confidence,
            cobitRef=parse_refs(raw.cobit_refs),
            cosoRef=parse_refs(raw.coso_refs),
            rgsiRef=parse_refs(raw.rgsi_refs),
            evidence=parse_evidence(raw.evidence),
            quote=raw.quote,
            detectedBy=f"COSFI-{raw.source_framework}",
            createdAt=now,
            updatedAt=now,
        )
