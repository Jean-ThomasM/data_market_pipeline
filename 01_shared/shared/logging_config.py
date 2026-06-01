"""Configuration de logging unifiée pour tous les extracteurs."""

import logging
import os
import sys
from datetime import datetime, timezone


def get_log_level() -> int:
    """Récupère le niveau de log depuis la variable d'environnement LOG_LEVEL."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def get_log_format() -> str:
    """Récupère le format de log depuis la variable d'environnement LOG_FORMAT."""
    return os.getenv(
        "LOG_FORMAT", "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )


def configure_logging(
    level: int | None = None,
    format_str: str | None = None,
    module_name: str | None = None,
) -> logging.Logger:
    """Configure le logging pour un module.

    Args:
        level: Niveau de logging (défaut: LOG_LEVEL env ou INFO)
        format_str: Format des logs (défaut: LOG_FORMAT env ou format standard)
        module_name: Nom du module pour le logger (défaut: appelant)

    Returns:
        Logger configuré
    """
    if level is None:
        level = get_log_level()

    if format_str is None:
        format_str = get_log_format()

    if module_name is None:
        # Récupère le nom du module appelant
        frame = sys._getframe(1)
        module = sys.modules.get(frame.f_globals.get("__name__", "__main__"))
        module_name = getattr(module, "__name__", "root")

    # Configure le handler de base
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(format_str)
    handler.setFormatter(formatter)

    # Configure le logger
    logger = logging.getLogger(module_name)
    logger.setLevel(level)

    # Évite les handlers dupliqués
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Récupère un logger déjà configuré ou le configure.

    Args:
        name: Nom du logger

    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)

    # Si pas encore configuré, applique la config par défaut
    if not logger.handlers:
        configure_logging(module_name=name)

    return logger


class StructuredLogFormatter(logging.Formatter):
    """Formatter pour logs structurés (JSON-like)."""

    def format(self, record: logging.LogRecord) -> str:
        """Formate le log en format structuré."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Ajoute les extras si présents
        if hasattr(record, "extras"):
            log_entry.update(record.extras)

        # Ajoute les exceptions si présentes
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return str(log_entry)


def configure_structured_logging(
    level: int | None = None, module_name: str | None = None
) -> logging.Logger:
    """Configure le logging structuré.

    Args:
        level: Niveau de logging
        module_name: Nom du module

    Returns:
        Logger configuré avec formatage structuré
    """
    if level is None:
        level = get_log_level()

    if module_name is None:
        frame = sys._getframe(1)
        module = sys.modules.get(frame.f_globals.get("__name__", "__main__"))
        module_name = getattr(module, "__name__", "root")

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = StructuredLogFormatter()
    handler.setFormatter(formatter)

    logger = logging.getLogger(module_name)
    logger.setLevel(level)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger
