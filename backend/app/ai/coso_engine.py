"""Motor IA para análisis COSO 2013."""

from typing import List

from app.ai.base_engine import BaseEngine
from app.ai.prompt_builder import build_coso_prompt
from app.ai.providers.gemini_provider import GeminiProvider, get_coso_provider


class COSOEngine(BaseEngine):
    framework = "COSO"

    def __init__(self, provider: GeminiProvider | None = None):
        super().__init__(provider or get_coso_provider())

    def build_prompt(self, text: str, prior_findings: List[dict], audit_meta: dict = None) -> str:
        return build_coso_prompt(text, prior_findings, audit_meta)
