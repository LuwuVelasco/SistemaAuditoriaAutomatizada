"""
Proveedor Ollama — instancia un cliente por framework para conectarse al modelo local (Qwen2.5-VL).
"""

from functools import lru_cache
from typing import List, Optional

import httpx
from loguru import logger

from app.core.config import settings


class OllamaProvider:
    """
    Wrapper sobre la API REST de Ollama.
    Una instancia por framework.
    """

    def __init__(self, framework: str):
        self._framework = framework
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_MODEL
        self._timeout = 300.0  # El modelo local puede tomar varios minutos
        logger.info(f"OllamaProvider inicializado para {framework.upper()} ({self._model})")

    async def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Envía el prompt a Ollama y retorna el texto generado.
        """
        return await self.generate_with_images(prompt, images=None, temperature=temperature)

    async def generate_with_images(
        self, prompt: str, images: Optional[List[str]] = None, temperature: float = 0.2
    ) -> str:
        """
        Envía texto e imágenes a Ollama.
        images: Lista de strings en base64 de las imágenes.
        """
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096,
            }
        }

        if images:
            payload["images"] = images

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "")
                
                logger.debug(
                    f"[{self._framework}] Ollama respondió: {len(text)} chars "
                    f"en {data.get('eval_duration', 0) / 1e9:.2f}s"
                )
                return text
        except Exception as exc:
            logger.error(f"[{self._framework}] Error Ollama: {exc}")
            raise


@lru_cache(maxsize=3)
def get_coso_provider() -> OllamaProvider:
    return OllamaProvider("coso")


@lru_cache(maxsize=3)
def get_cobit_provider() -> OllamaProvider:
    return OllamaProvider("cobit")


@lru_cache(maxsize=3)
def get_rgsi_provider() -> OllamaProvider:
    return OllamaProvider("rgsi")
