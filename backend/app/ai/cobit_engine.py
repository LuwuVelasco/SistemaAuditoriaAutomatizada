"""Motor IA para análisis COBIT 2019."""

from typing import List

from app.ai.base_engine import BaseEngine
from app.ai.prompt_builder import build_cobit_prompt
from app.ai.providers.ollama_provider import OllamaProvider, get_cobit_provider


class COBITEngine(BaseEngine):
    framework = "COBIT"

    def __init__(self, provider: OllamaProvider | None = None):
        super().__init__(provider or get_cobit_provider())

    def build_prompt(self, text: str, prior_findings: List[dict]) -> str:
        return build_cobit_prompt(text, prior_findings)
