"""Configuración de logging con loguru."""

import sys

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """Configura el logger global de la aplicación."""
    logger.remove()

    log_level = "DEBUG" if settings.DEBUG else "INFO"

    # Console handler
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        enqueue=True,
    )

    # File handler — errores
    if settings.is_production:
        logger.add(
            "logs/saam_errors.log",
            level="ERROR",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            serialize=True,
        )
        logger.add(
            "logs/saam_app.log",
            level="INFO",
            rotation="50 MB",
            retention="7 days",
            compression="zip",
        )

    logger.info(f"Logging configurado — nivel: {log_level}, entorno: {settings.APP_ENV}")
