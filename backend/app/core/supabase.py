"""Inicialización y acceso al cliente Supabase."""

from loguru import logger
from supabase import Client, create_client
import os
from pathlib import Path
from dotenv import load_dotenv

from app.core.config import settings

# Ensure env file values (including VITE_*) are available to os.environ
env_file = Path(settings.model_config.get("env_file") or "")
if env_file.exists():
    load_dotenv(dotenv_path=str(env_file), override=False)

_supabase_client: Client | None = None


def _resolve_supabase_creds() -> tuple[str | None, str | None]:
    # Backend should prefer server-side keys first.
    url = (
        (settings.SUPABASE_URL if hasattr(settings, 'SUPABASE_URL') else None)
        or os.getenv("SUPABASE_URL")
        or os.getenv("VITE_SUPABASE_URL")
    )
    key = (
        (settings.SUPABASE_KEY if hasattr(settings, 'SUPABASE_KEY') else None)
        or os.getenv("SUPABASE_KEY")
        or os.getenv("VITE_SUPABASE_ANON_KEY")
    )

    # `sb_publishable_*` keys are intended for browser clients and may fail with
    # supabase-py, which expects anon/service_role API keys in backend contexts.
    if key and key.startswith("sb_publishable_"):
        return url, None

    return url, key


def get_supabase_client() -> Client:
    """Devuelve el cliente Supabase (singleton)."""
    global _supabase_client
    if _supabase_client is None:
        url, key = _resolve_supabase_creds()
        if not url or not key:
            raise RuntimeError(
                "Supabase no configurado para backend. Define SUPABASE_URL y SUPABASE_KEY "
                "(anon/service_role) en .env. No uses VITE_SUPABASE_ANON_KEY para el cliente Python."
            )
        _supabase_client = create_client(url, key)
        logger.info("Cliente Supabase inicializado.")
    return _supabase_client
