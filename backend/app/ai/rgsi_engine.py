"""Motor IA para análisis RGSI-ASFI."""

from typing import List

from app.ai.base_engine import BaseEngine
from app.ai.prompt_builder import build_rgsi_prompt
from app.ai.providers.ollama_provider import OllamaProvider, get_rgsi_provider


class RGSIEngine(BaseEngine):
    framework = "RGSI"

    def __init__(self, provider: OllamaProvider | None = None):
        super().__init__(provider or get_rgsi_provider())

    def build_prompt(self, text: str, prior_findings: List[dict]) -> str:
        return build_rgsi_prompt(text, prior_findings)
