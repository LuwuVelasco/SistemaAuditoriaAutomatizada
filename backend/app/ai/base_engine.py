"""Clase base abstracta para los motores IA."""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, List

from loguru import logger

from app.ai.providers.gemini_provider import GeminiProvider
from app.schemas.ai import RawFinding


class BaseEngine(ABC):
    """
    Define el contrato que deben implementar COSO, COBIT y RGSI engines.
    Gestiona el parsing robusto de la respuesta JSON de Gemini.
    """

    framework: str = ""

    def __init__(self, provider: GeminiProvider):
        self._provider = provider

    @abstractmethod
    def build_prompt(self, text: str, prior_findings: List[dict]) -> str:
        """Construye el prompt específico del framework."""

    async def analyze(self, text: str, prior_findings: List[dict] = None) -> List[RawFinding]:
        """
        Ejecuta el análisis sobre el texto y retorna hallazgos crudos.
        prior_findings: hallazgos ya identificados por motores previos en la cadena.
        """
        if not text.strip():
            logger.warning(f"[{self.framework}] Texto vacío — se omite análisis.")
            return []

        prompt = self.build_prompt(text, prior_findings or [])
        logger.info(f"[{self.framework}] Iniciando análisis ({len(text)} chars de texto)…")

        raw_response = await self._provider.generate(prompt)
        findings = self._parse_response(raw_response)

        logger.info(f"[{self.framework}] {len(findings)} hallazgos identificados.")
        return findings

    def _parse_response(self, raw: str) -> List[RawFinding]:
        """
        Parsea la respuesta de Gemini en objetos RawFinding.
        Maneja JSON parcial, markdown fences y errores de formato.
        """
        raw = (raw or "").strip()

        findings = []
        discarded = 0

        for item, error in self._iter_candidate_items(raw):
            if not isinstance(item, dict):
                discarded += 1
                continue
            try:
                normalized = self._normalize_item(item)
                normalized["source_framework"] = self.framework
                findings.append(RawFinding(**normalized))
            except Exception as exc:
                discarded += 1
                logger.warning(
                    f"[{self.framework}] Hallazgo descartado por error: {exc}"
                    + (f" | candidato: {error}" if error else "")
                )

        logger.info(
            f"[{self.framework}] Parseo completado: {len(findings)} válidos, {discarded} descartados."
        )
        if not findings and raw:
            logger.debug(f"[{self.framework}] Respuesta cruda (preview): {raw[:1200]}")
        return findings

    def _iter_candidate_items(self, raw: str) -> list[tuple[Any, str]]:
        """
        Devuelve candidatos JSON recuperables.
        Primero intenta extraer un bloque JSON completo; si falla, rescata
        objetos de nivel superior uno por uno para no perder todo el lote.
        """
        candidates: list[tuple[Any, str]] = []
        payloads = self._extract_json_payloads(raw)

        for payload in payloads:
            parsed = self._load_json_best_effort(payload)
            if isinstance(parsed, dict) and "findings" in parsed:
                findings = parsed.get("findings", [])
                if isinstance(findings, list):
                    for item in findings:
                        candidates.append((item, "findings[]"))
                continue
            if isinstance(parsed, list):
                for item in parsed:
                    candidates.append((item, "array"))
                continue
            if isinstance(parsed, dict):
                candidates.append((parsed, "object"))
                continue

            # Fallback: intentar recuperar objetos de nivel superior dentro del array.
            for obj_text in self._split_top_level_objects(payload):
                obj = self._load_json_best_effort(obj_text)
                candidates.append((obj, obj_text[:120]))

        if not candidates and raw:
            # Último recurso: tratar todo el texto como un solo objeto si parece JSON.
            obj = self._load_json_best_effort(raw)
            if isinstance(obj, dict):
                candidates.append((obj, "raw"))

        return candidates

    def _extract_json_payloads(self, raw: str) -> list[str]:
        """Extrae uno o más bloques JSON candidatos desde texto crudo."""
        payloads: list[str] = []

        fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
        if fenced:
            payloads.extend(fenced)

        if not payloads:
            balanced = self._find_balanced_json_block(raw)
            if balanced:
                payloads.append(balanced)
            else:
                json_match = re.search(r"\[[\s\S]*\]", raw)
                if json_match:
                    payloads.append(json_match.group())

        return payloads

    def _load_json_best_effort(self, text: str) -> Any:
        """Intenta cargar JSON aplicando reparaciones menores primero."""
        if not text:
            return None

        for candidate in (text, self._repair_json(text), self._repair_json(self._normalize_quotes(text))):
            try:
                return json.loads(candidate)
            except Exception:
                continue
        return None

    @staticmethod
    def _normalize_quotes(raw: str) -> str:
        """Normaliza comillas tipográficas que a veces devuelve el modelo."""
        return (
            raw.replace("“", '"')
            .replace("”", '"')
            .replace("«", '"')
            .replace("»", '"')
            .replace("’", "'")
        )

    def _find_balanced_json_block(self, raw: str) -> str | None:
        """Devuelve el primer bloque JSON balanceado que encuentre en el texto."""
        start = None
        stack = []
        in_string = False
        escape = False

        for idx, ch in enumerate(raw):
            if start is None:
                if ch in "[{":
                    start = idx
                    stack.append(ch)
                continue

            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch in "[{":
                stack.append(ch)
            elif ch in "]}":
                if not stack:
                    continue
                opener = stack.pop()
                if (opener == "[" and ch != "]") or (opener == "{" and ch != "}"):
                    continue
                if not stack:
                    return raw[start: idx + 1]

        return None

    def _split_top_level_objects(self, raw: str) -> list[str]:
        """
        Divide un array JSON en objetos de nivel superior.
        Sirve para rescatar hallazgos completos aunque el array esté roto.
        """
        objects: list[str] = []
        start = None
        depth = 0
        in_string = False
        escape = False

        for idx, ch in enumerate(raw):
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue

            if ch == "{":
                if depth == 0:
                    start = idx
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        objects.append(raw[start:idx + 1])
                        start = None

        return objects

    @staticmethod
    def _repair_json(raw: str) -> str:
        """Repara problemas menores de JSON sin introducir nuevas llamadas al modelo."""
        repaired = raw.strip()
        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
        repaired = re.sub(r"'([^']+)'\s*:", r'"\1":', repaired)
        return repaired

    def _normalize_item(self, item: dict) -> dict:
        """Normaliza variantes comunes de campos devueltos por LLMs."""
        normalized = dict(item)

        # Alias frecuentes
        if "description_finding" not in normalized and normalized.get("description"):
            normalized["description_finding"] = normalized.get("description")
        if "criteria_description" not in normalized and normalized.get("criteria"):
            normalized["criteria_description"] = normalized.get("criteria")
        if "recommendation" not in normalized and normalized.get("recommendations"):
            normalized["recommendation"] = normalized.get("recommendations")

        # Campos mínimos para no descartar por ausencias menores
        normalized.setdefault("description_finding", "")
        normalized.setdefault("criteria_description", "")
        normalized.setdefault("cause", "")
        normalized.setdefault("effect", "")
        normalized.setdefault("conclusion", "")
        normalized.setdefault("recommendation", "Revisar el proceso y fortalecer controles.")

        # Confidence: aceptar 0-1, 0-100 o string numérico
        conf = normalized.get("confidence", 0.75)
        try:
            conf = float(conf)
            if conf > 1.0:
                conf = conf / 100.0
            conf = max(0.0, min(1.0, conf))
        except Exception:
            conf = 0.75
        normalized["confidence"] = conf

        # Risk level tolerante a mayúsculas/minúsculas
        risk = str(normalized.get("risk_level", "Medio") or "Medio").strip().capitalize()
        if risk not in {"Bajo", "Medio", "Alto", "Extremo", "Oportunidad"}:
            risk = "Medio"
        normalized["risk_level"] = risk

        # Listas opcionales
        for k in ("cobit_refs", "coso_refs", "rgsi_refs", "evidence"):
            v = normalized.get(k, [])
            normalized[k] = v if isinstance(v, list) else []

        return normalized
