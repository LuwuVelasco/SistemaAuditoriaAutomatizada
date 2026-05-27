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

        # Intento 1: parsear directo (a veces Gemini devuelve JSON puro).
        parsed: Any = None
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None

        # Intento 2: extraer JSON en markdown fence ```json ... ```
        if parsed is None:
            fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
            if fenced:
                try:
                    parsed = json.loads(fenced.group(1))
                except Exception:
                    parsed = None

        # Intento 3: extraer primer array JSON dentro del texto.
        if parsed is None:
            json_match = re.search(r"\[[\s\S]*\]", raw)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError as exc:
                    logger.error(f"[{self.framework}] JSON inválido: {exc}")
                    return []

        if parsed is None:
            logger.warning(f"[{self.framework}] No se encontró JSON parseable en la respuesta.")
            return []

        # Permitir salida tipo {"findings": [...]} además de [...]
        if isinstance(parsed, dict):
            data = parsed.get("findings", [])
        elif isinstance(parsed, list):
            data = parsed
        else:
            logger.warning(f"[{self.framework}] JSON con formato no soportado: {type(parsed).__name__}")
            return []

        findings = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                item = self._normalize_item(item)
                item["source_framework"] = self.framework
                findings.append(RawFinding(**item))
            except Exception as exc:
                logger.warning(f"[{self.framework}] Hallazgo descartado por error: {exc}")

        return findings

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
