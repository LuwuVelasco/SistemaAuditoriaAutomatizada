"""Configuración central de la aplicación vía variables de entorno.

Esta versión fuerza la carga desde el `.env` del directorio `backend/`
y no contiene valores por defecto incrustados para credenciales sensibles.
Se normalizan rutas relativas respecto a `backend/` cuando procede.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "SAAM Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ── Firebase ─────────────────────────────────────────────────────────────
    # These values are loaded from backend/.env. Leave unset here to force
    # developers to provide them via the environment file or env vars.
    FIREBASE_CREDENTIALS_PATH: str | None = None
    FIREBASE_PROJECT_ID: str | None = None
    FIREBASE_CLIENT_EMAIL: str | None = None
    FIREBASE_PRIVATE_KEY: str | None = None

    # ── Supabase ─────────────────────────────────────────────────────────────
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_BUCKET_PDFS: str = "pdfs"
    SUPABASE_BUCKET_XLSX: str = "xlsx"

    # ── Gemini (3 keys independientes) ───────────────────────────────────────
    GEMINI_COSO_API_KEY: str | None = None
    GEMINI_COBIT_API_KEY: str | None = None
    GEMINI_RGSI_API_KEY: str | None = None

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @field_validator("FIREBASE_CREDENTIALS_PATH", mode="before")
    @classmethod
    def normalize_firebase_credentials_path(cls, v: str | None) -> str:
        if not v:
            return ""
        p = Path(v).expanduser()
        if p.is_absolute():
            return str(p)
        # resolve relative paths against backend dir (where .env lives)
        candidate = (_BACKEND_DIR / p).resolve()
        return str(candidate)

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
