"""
Consolidador de hallazgos multimarco.

Objetivo:
- Eliminar duplicados (mismo problema identificado por varios motores)
- Fusionar referencias normativas (COBIT + COSO + RGSI en un solo hallazgo)
- Unificar recomendaciones
- Preservar la evidencia de todos los motores que detectaron el hallazgo
"""

from typing import List

from loguru import logger

from app.ai.semantic_similarity import are_duplicates
from app.schemas.ai import RawFinding


class FindingMerger:
    """
    Consolida listas de RawFinding de los tres motores en hallazgos unificados.
    """

    DUPLICATE_THRESHOLD = 0.45   # Similitud Jaccard mínima para considerar duplicado

    def merge(self, all_findings: List[RawFinding]) -> List[RawFinding]:
        """
        Punto de entrada principal.
        Recibe todos los hallazgos crudos (de los N motores ejecutados)
        y retorna la lista consolidada.
        """
        if not all_findings:
            return []

        consolidated: List[RawFinding] = []

        for candidate in all_findings:
            merged = False
            for existing in consolidated:
                if self._should_merge(candidate, existing):
                    self._merge_into(existing, candidate)
                    merged = True
                    break
            if not merged:
                consolidated.append(candidate)

        logger.info(
            f"Merger: {len(all_findings)} hallazgos crudos → {len(consolidated)} consolidados."
        )
        return consolidated

    def _should_merge(self, a: RawFinding, b: RawFinding) -> bool:
        """Determina si dos hallazgos deben fusionarse."""
        # Comparar título + descripción concatenados para mayor precisión
        text_a = f"{a.title} {a.description_finding or a.conclusion}"
        text_b = f"{b.title} {b.description_finding or b.conclusion}"
        return are_duplicates(text_a, text_b, self.DUPLICATE_THRESHOLD)

    def _merge_into(self, target: RawFinding, source: RawFinding) -> None:
        """
        Fusiona `source` dentro de `target`:
        - Une referencias normativas
        - Combina evidencias
        - Promedia confianza
        - Usa el riesgo más alto
        - Conserva la mejor recomendación (la más larga/detallada)
        """
        # Fusionar referencias (sin duplicados por código)
        target.cobit_refs = self._merge_refs(target.cobit_refs, source.cobit_refs)
        target.coso_refs  = self._merge_refs(target.coso_refs,  source.coso_refs)
        target.rgsi_refs  = self._merge_refs(target.rgsi_refs,  source.rgsi_refs)

        # Combinar evidencias
        target.evidence = list({
            str(e): e for e in (target.evidence + source.evidence)
        }.values())

        # Promediar confianza (ponderar hacia el valor más alto)
        target.confidence = max(target.confidence, source.confidence)

        # Riesgo más conservador (más alto)
        target.risk_level = self._higher_risk(target.risk_level, source.risk_level)

        # Recomendación más completa
        if len(source.recommendation) > len(target.recommendation):
            target.recommendation = source.recommendation

        # Conservar campos analíticos más completos
        target.description_finding = self._prefer_longer(target.description_finding, source.description_finding)
        target.criteria_description = self._prefer_longer(target.criteria_description, source.criteria_description)
        target.cause = self._prefer_longer(target.cause, source.cause)
        target.effect = self._prefer_longer(target.effect, source.effect)
        target.conclusion = self._prefer_longer(target.conclusion, source.conclusion)

        # Quote: conservar si no hay uno aún
        if not target.quote and source.quote:
            target.quote = source.quote

        # Marcar como detectado por múltiples motores
        target.source_framework = f"{target.source_framework}+{source.source_framework}"

    @staticmethod
    def _merge_refs(existing: List[dict], incoming: List[dict]) -> List[dict]:
        """Une referencias eliminando duplicados por código."""
        existing_codes = {r.get("code") for r in existing}
        for ref in incoming:
            if ref.get("code") not in existing_codes:
                existing.append(ref)
                existing_codes.add(ref.get("code"))
        return existing

    _RISK_ORDER = {"Bajo": 1, "Medio": 2, "Alto": 3, "Extremo": 4}

    def _higher_risk(self, a: str, b: str) -> str:
        order = self._RISK_ORDER
        return a if order.get(a, 2) >= order.get(b, 2) else b

    @staticmethod
    def _prefer_longer(current: str, incoming: str) -> str:
        if not current:
            return incoming or current
        if incoming and len(incoming) > len(current):
            return incoming
        return current
