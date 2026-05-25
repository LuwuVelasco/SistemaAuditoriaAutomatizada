"""
Similitud semántica para detección de hallazgos duplicados.

Implementación inicial: similitud de Jaccard sobre tokens de texto.
Arquitectura preparada para reemplazar con embeddings + cosine similarity
cuando se integre un vector store (Vertex AI, Supabase pgvector, etc.).
"""

import re
from typing import List, Set

from loguru import logger


def _tokenize(text: str) -> Set[str]:
    """Convierte texto a conjunto de tokens (palabras, sin stopwords básicas)."""
    STOPWORDS = {
        "de", "la", "el", "en", "y", "a", "los", "las", "que", "se",
        "un", "una", "con", "por", "para", "del", "al", "es", "no",
        "su", "sus", "son", "han", "más", "como", "una", "este", "esta",
    }
    tokens = re.findall(r"[a-záéíóúüñ]+", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """
    Similitud de Jaccard entre dos textos.
    Retorna valor entre 0.0 (sin similitud) y 1.0 (idénticos).
    """
    set_a = _tokenize(text_a)
    set_b = _tokenize(text_b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def are_duplicates(text_a: str, text_b: str, threshold: float = 0.45) -> bool:
    """Determina si dos textos son suficientemente similares para considerarse duplicados."""
    score = jaccard_similarity(text_a, text_b)
    return score >= threshold


# ── Placeholder para embeddings futuros ──────────────────────────────────────

def cosine_similarity_embeddings(emb_a: List[float], emb_b: List[float]) -> float:
    """
    Similitud coseno entre dos vectores de embeddings.
    Activar cuando se integre generación de embeddings (Gemini text-embedding-004,
    Vertex AI, etc.).
    """
    if len(emb_a) != len(emb_b):
        raise ValueError("Los embeddings deben tener la misma dimensión.")
    dot = sum(a * b for a, b in zip(emb_a, emb_b))
    norm_a = sum(a ** 2 for a in emb_a) ** 0.5
    norm_b = sum(b ** 2 for b in emb_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
