"""
Matriz de riesgo: calcula el nivel a partir de impacto × probabilidad.

Escala de cada dimensión: 1 (mínimo) → 5 (máximo).
Puntuación compuesta (1–25):

  1 – 4   → Bajo
  5 – 9   → Medio
 10 – 16  → Alto
 17 – 25  → Extremo
"""

from app.utils.enums import RiskLevel


def calculate_risk(impact: int, probability: int) -> RiskLevel:
    """Determina el nivel de riesgo dado impacto y probabilidad (1-5 cada uno)."""
    if not (1 <= impact <= 5 and 1 <= probability <= 5):
        raise ValueError("Impacto y probabilidad deben estar entre 1 y 5.")

    score = impact * probability

    if score <= 4:
        return RiskLevel.BAJO
    elif score <= 9:
        return RiskLevel.MEDIO
    elif score <= 16:
        return RiskLevel.ALTO
    else:
        return RiskLevel.EXTREMO


def risk_score(impact: int, probability: int) -> int:
    """Puntuación numérica compuesta (1–25) para ordenamiento."""
    return impact * probability


RISK_COLOR_MAP: dict[RiskLevel, str] = {
    RiskLevel.BAJO: "#22c55e",
    RiskLevel.MEDIO: "#eab308",
    RiskLevel.ALTO: "#f97316",
    RiskLevel.EXTREMO: "#ef4444",
    RiskLevel.OPORTUNIDAD: "#22d3ee",
}
