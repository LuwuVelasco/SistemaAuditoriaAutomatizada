"""Clase base abstracta para los motores IA."""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, List

from loguru import logger

from app.ai.providers.ollama_provider import OllamaProvider
from app.schemas.ai import RawFinding


class BaseEngine(ABC):
    """
    Define el contrato que deben implementar COSO, COBIT y RGSI engines.
    Gestiona el parsing robusto de la respuesta JSON de Gemini.
    """

    framework: str = ""

    def __init__(self, provider: OllamaProvider):
        self._provider = provider

    @abstractmethod
    def build_prompt(self, text: str, prior_findings: List[dict]) -> str:
        """Construye el prompt específico del framework."""

    async def analyze(self, text: str, prior_findings: List[dict] = None, images: List[str] = None) -> List[RawFinding]:
        """
        Ejecuta el análisis sobre el texto y retorna hallazgos crudos.
        prior_findings: hallazgos ya identificados por motores previos en la cadena.
        """
        if not text.strip() and not images:
            logger.warning(f"[{self.framework}] Texto e imágenes vacíos — se omite análisis.")
            return []

        prompt = self.build_prompt(text, prior_findings or [])
        logger.info(f"[{self.framework}] Iniciando análisis ({len(text)} chars de texto, {len(images or [])} imágenes)…")

        if images:
            raw_response = await self._provider.generate_with_images(prompt, images=images)
        else:
            raw_response = await self._provider.generate(prompt)
            
        findings = self._parse_response(raw_response)

        logger.info(f"[{self.framework}] {len(findings)} hallazgos identificados.")
        return findings

    def _parse_response(self, raw: str) -> List[RawFinding]:
        """
        Parsea la respuesta de Gemini en objetos RawFinding.
        Maneja JSON parcial, markdown fences y errores de formato.
        """
        # Extraer bloque JSON
        json_match = re.search(r"\[[\s\S]*\]", raw)
        if not json_match:
            logger.warning(f"[{self.framework}] No se encontró JSON en la respuesta.")
            return []

        try:
            data: List[Any] = json.loads(json_match.group())
        except json.JSONDecodeError as exc:
            logger.error(f"[{self.framework}] JSON inválido: {exc}")
            return []

        findings = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                item["source_framework"] = self.framework
                findings.append(RawFinding(**item))
            except Exception as exc:
                logger.warning(f"[{self.framework}] Hallazgo descartado por error: {exc}")

        return findings
