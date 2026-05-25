"""Inicialización y acceso al cliente Supabase."""

from loguru import logger
from supabase import Client, create_client

from app.core.config import settings

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Devuelve el cliente Supabase (singleton)."""
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError(
                "Supabase no configurado. Define SUPABASE_URL y SUPABASE_KEY en .env."
            )
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Cliente Supabase inicializado.")
    return _supabase_client
