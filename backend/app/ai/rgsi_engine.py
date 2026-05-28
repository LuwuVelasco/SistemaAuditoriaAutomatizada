"""Motor IA para análisis RGSI-ASFI."""

from typing import List

from app.ai.base_engine import BaseEngine
from app.ai.prompt_builder import build_rgsi_prompt
from app.ai.providers.gemini_provider import GeminiProvider, get_rgsi_provider


class RGSIEngine(BaseEngine):
    framework = "RGSI"

    def __init__(self, provider: GeminiProvider | None = None):
        super().__init__(provider or get_rgsi_provider())

    def build_prompt(self, text: str, prior_findings: List[dict], audit_meta: dict = None) -> str:
        return build_rgsi_prompt(text, prior_findings, audit_meta)
