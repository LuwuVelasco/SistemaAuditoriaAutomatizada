"""
Orquestador del pipeline IA multimarco.

Secuencia FIJA (según RGSI-ASFI, las regulaciones locales tienen precedencia):
  1. COSO  — analiza primero
  2. COBIT — recibe hallazgos COSO como contexto
  3. RGSI  — recibe hallazgos COSO + COBIT como contexto

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
from app.models.finding import Finding, NormativeRef
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

        # Motor 1: COSO
        if "COSO" in framework_values:
            coso_results = await self._coso.analyze(text, prior_findings=prior_dicts)
            all_raw.extend(coso_results)
            prior_dicts.extend([r.model_dump() for r in coso_results])
            logger.info(f"[COSO] {len(coso_results)} hallazgos.")

        # Motor 2: COBIT (recibe contexto COSO si fue ejecutado)
        if "COBIT" in framework_values:
            cobit_results = await self._cobit.analyze(text, prior_findings=prior_dicts)
            all_raw.extend(cobit_results)
            prior_dicts.extend([r.model_dump() for r in cobit_results])
            logger.info(f"[COBIT] {len(cobit_results)} hallazgos.")

        # Motor 3: RGSI (recibe contexto COSO + COBIT)
        if "RGSI" in framework_values:
            rgsi_results = await self._rgsi.analyze(text, prior_findings=prior_dicts)
            all_raw.extend(rgsi_results)
            logger.info(f"[RGSI] {len(rgsi_results)} hallazgos.")

        # ── 3. Consolidación y deduplicación ─────────────────────────────────
        consolidated = self._merger.merge(all_raw)

        # ── 4. Convertir a Finding del dominio ───────────────────────────────
        findings = [
            self._raw_to_finding(audit_id, raw)
            for raw in consolidated
        ]

        logger.info(
            f"[Orquestador] Pipeline completado: {len(all_raw)} crudos → "
            f"{len(findings)} hallazgos finales para auditoría {audit_id}."
        )
        return findings

    def _raw_to_finding(self, audit_id: str, raw: RawFinding) -> Finding:
        """Convierte un RawFinding (salida del motor) a Finding (modelo de dominio)."""
        now = utcnow_iso()
        finding_id = generate_id("HLZ-")

        # Usar impact=4 / probability=3 como valores iniciales para riesgo "Alto"
        # El auditor los ajustará en la UI.
        RISK_TO_IMPACT = {"Bajo": 2, "Medio": 3, "Alto": 4, "Extremo": 5}
        impact = RISK_TO_IMPACT.get(raw.risk_hint, 3)
        probability = RISK_TO_IMPACT.get(raw.risk_hint, 3) - 1 or 1
        risk = calculate_risk(impact, probability)

        def parse_refs(raw_list: List[dict]) -> List[NormativeRef]:
            result = []
            for r in raw_list:
                try:
                    result.append(NormativeRef(**r))
                except Exception:
                    pass
            return result

        return Finding(
            id=finding_id,
            auditId=audit_id,
            title=raw.title,
            description=raw.description,
            recommendation=raw.recommendation,
            risk=risk,
            impact=impact,
            probability=probability,
            status=FindingStatus.PENDIENTE,
            confidence=raw.confidence,
            cobitRef=parse_refs(raw.cobit_refs),
            cosoRef=parse_refs(raw.coso_refs),
            rgsiRef=parse_refs(raw.rgsi_refs),
            evidence=[],
            quote=raw.quote,
            detectedBy=f"COSFI-{raw.source_framework}",
            createdAt=now,
            updatedAt=now,
        )
