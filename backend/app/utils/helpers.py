"""Funciones utilitarias generales."""

import re
import unicodedata
import uuid
from typing import Any


def generate_id(prefix: str = "") -> str:
    """Genera un ID único corto con prefijo opcional (ej. 'aud-a3f8b1')."""
    short = str(uuid.uuid4()).replace("-", "")[:8]
    return f"{prefix}{short}" if prefix else short


def strip_none(d: dict) -> dict:
    """Elimina claves con valor None de un diccionario (para Firestore)."""
    return {k: v for k, v in d.items() if v is not None}


def normalize_text(text: str) -> str:
    """Normaliza texto: elimina caracteres de control, colapsa espacios."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
    """
    Divide texto en fragmentos con solapamiento para procesamiento IA.
    chunk_size y overlap en caracteres.
    """
    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        if end == length:
            break
        start = end - overlap

    return chunks


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convierte a float de forma segura."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convierte a int de forma segura."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
