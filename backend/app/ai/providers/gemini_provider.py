"""
Proveedor Gemini — instancia un cliente por framework con su API key dedicada.
Cada motor (COSO, COBIT, RGSI) usa su propia key para trazabilidad de uso.
"""

from functools import lru_cache
from typing import Optional

import google.generativeai as genai
from loguru import logger

from app.core.config import settings

_MODEL = "gemini-2.0-flash"


class GeminiProvider:
    """
    Wrapper sobre el SDK de Gemini que gestiona el modelo y las llamadas.
    Una instancia por framework.
    """

    def __init__(self, api_key: str, framework: str):
        if not api_key:
            raise ValueError(
                f"GEMINI_{framework.upper()}_API_KEY no está configurada. "
                "Verifica tu archivo .env."
            )
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name=_MODEL)
        self._framework = framework
        logger.info(f"GeminiProvider inicializado para {framework.upper()} ({_MODEL})")

    async def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Envía el prompt a Gemini y retorna el texto generado.
        temperature baja = respuestas más consistentes y formales.
        """
        config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=8192,
        )
        try:
            response = self._model.generate_content(prompt, generation_config=config)
            text = response.text
            logger.debug(
                f"[{self._framework}] Gemini respondió: {len(text)} chars "
                f"(tokens aprox. {len(text) // 4})"
            )
            return text
        except Exception as exc:
            logger.error(f"[{self._framework}] Error Gemini: {exc}")
            raise


@lru_cache(maxsize=3)
def get_coso_provider() -> GeminiProvider:
    return GeminiProvider(settings.GEMINI_COSO_API_KEY, "coso")


@lru_cache(maxsize=3)
def get_cobit_provider() -> GeminiProvider:
    return GeminiProvider(settings.GEMINI_COBIT_API_KEY, "cobit")


@lru_cache(maxsize=3)
def get_rgsi_provider() -> GeminiProvider:
    return GeminiProvider(settings.GEMINI_RGSI_API_KEY, "rgsi")
