"""
Proveedor Gemini — instancia un cliente por framework con su API key dedicada.
Cada motor (COSO, COBIT, RGSI) usa su propia key para trazabilidad de uso.
"""

import asyncio
import re
import time
from functools import lru_cache
from typing import Optional

import google.generativeai as genai
from loguru import logger

from app.core.config import settings

_MODEL = "gemini-2.5-flash"
_GEMINI_COOLDOWN_UNTIL = 0.0
_GEMINI_COOLDOWN_LOCK = asyncio.Lock()
_GEMINI_CLIENT_LOCK = asyncio.Lock()


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
        self._api_key = api_key
        self._framework = framework
        logger.info(f"GeminiProvider inicializado para {framework.upper()} ({_MODEL})")

    async def generate(self, prompt: str, temperature: float = 0.2, json_mode: bool = True) -> str:
        """
        Envía el prompt a Gemini y retorna el texto generado.
        json_mode=False para respuestas de texto libre (chatbot).
        """
        config_kwargs = dict(temperature=temperature, max_output_tokens=8192)
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"
        config = genai.types.GenerationConfig(**config_kwargs)
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                await self._respect_global_cooldown()
                async with _GEMINI_CLIENT_LOCK:
                    genai.configure(api_key=self._api_key)
                    model = genai.GenerativeModel(model_name=_MODEL)
                    response = model.generate_content(prompt, generation_config=config)
                text = response.text or ""
                logger.debug(
                    f"[{self._framework}] Gemini respondió: {len(text)} chars "
                    f"(tokens aprox. {len(text) // 4})"
                )
                if settings.GEMINI_LOG_RESPONSES:
                    preview = text.replace("\n", " ")[:1200]
                    logger.info(
                        f"[{self._framework}] Gemini response preview (1200 chars max): {preview}"
                    )
                return text
            except Exception as exc:
                retry_delay = self._extract_retry_delay_seconds(exc)
                is_quota_error = self._is_quota_error(exc)

                if is_quota_error and attempt < max_attempts:
                    wait_seconds = retry_delay or self._backoff_seconds(attempt)
                    self._set_global_cooldown(wait_seconds)
                    logger.warning(
                        f"[{self._framework}] Cuota Gemini excedida. "
                        f"Reintentando en {wait_seconds:.1f}s (intento {attempt}/{max_attempts})."
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"[{self._framework}] Error Gemini: {exc}")
                raise

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        message = str(exc)
        return "429" in message or "quota exceeded" in message.lower() or "rate limits" in message.lower()

    @staticmethod
    def _extract_retry_delay_seconds(exc: Exception) -> Optional[float]:
        message = str(exc)
        match = re.search(r"retry_delay[^0-9]*seconds:\s*([0-9]+(?:\.[0-9]+)?)", message, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        match = re.search(r"Please retry in ([0-9]+(?:\.[0-9]+)?)s", message, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    @staticmethod
    def _backoff_seconds(attempt: int) -> float:
        # Backoff corto y creciente para no martillar la cuota.
        return min(60.0, 5.0 * (2 ** (attempt - 1)))

    async def _respect_global_cooldown(self) -> None:
        global _GEMINI_COOLDOWN_UNTIL
        now = time.monotonic()
        async with _GEMINI_COOLDOWN_LOCK:
            wait_seconds = _GEMINI_COOLDOWN_UNTIL - now
        if wait_seconds > 0:
            logger.warning(
                f"[{self._framework}] Esperando {wait_seconds:.1f}s por cooldown global de Gemini."
            )
            await asyncio.sleep(wait_seconds)

    def _set_global_cooldown(self, seconds: float) -> None:
        global _GEMINI_COOLDOWN_UNTIL
        _GEMINI_COOLDOWN_UNTIL = time.monotonic() + max(0.0, seconds)


@lru_cache(maxsize=3)
def get_coso_provider() -> GeminiProvider:
    return GeminiProvider(settings.GEMINI_COSO_API_KEY, "coso")


@lru_cache(maxsize=3)
def get_cobit_provider() -> GeminiProvider:
    return GeminiProvider(settings.GEMINI_COBIT_API_KEY, "cobit")


@lru_cache(maxsize=3)
def get_rgsi_provider() -> GeminiProvider:
    return GeminiProvider(settings.GEMINI_RGSI_API_KEY, "rgsi")


@lru_cache(maxsize=1)
def get_chat_provider() -> GeminiProvider:
    return GeminiProvider(settings.GEMINI_CHAT_API_KEY, "chat")
