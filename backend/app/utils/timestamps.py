"""Utilidades de fecha/hora en UTC."""

from datetime import datetime, timezone


def utcnow_iso() -> str:
    """Timestamp ISO 8601 en UTC, e.g. '2025-01-20T14:00:00+00:00'."""
    return datetime.now(timezone.utc).isoformat()


def utcnow() -> datetime:
    """Objeto datetime en UTC timezone-aware."""
    return datetime.now(timezone.utc)


def format_date(dt: datetime) -> str:
    """Formatea como 'YYYY-MM-DD'."""
    return dt.strftime("%Y-%m-%d")
