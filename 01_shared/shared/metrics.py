"""Module de collecte de métriques et monitoring pour les extracteurs."""

import functools
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypeVar

from shared.logging_config import get_logger

logger = get_logger("metrics")

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class ApiCallMetrics:
    """Métriques pour un appel API."""

    endpoint: str
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    duration_ms: float = 0.0
    status_code: int | None = None
    success: bool = False
    error_message: str | None = None
    records_count: int = 0
    retry_count: int = 0

    def complete(
        self,
        success: bool = True,
        status_code: int | None = None,
        records_count: int = 0,
        error_message: str | None = None,
    ) -> None:
        """Marque l'appel comme terminé et calcule les métriques."""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.success = success
        self.status_code = status_code
        self.records_count = records_count
        self.error_message = error_message

        self._log()

    def _log(self) -> None:
        """Log les métriques de l'appel."""
        status = "SUCCESS" if self.success else "FAILURE"
        logger.info(
            f"API Call {status} | {self.endpoint} | "
            f"duration={self.duration_ms:.2f}ms | "
            f"status_code={self.status_code} | "
            f"records={self.records_count} | "
            f"retries={self.retry_count}"
        )


@dataclass
class ExtractionMetrics:
    """Métriques globales pour une extraction."""

    extractor_name: str
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    total_api_calls: int = 0
    successful_api_calls: int = 0
    failed_api_calls: int = 0
    total_records_fetched: int = 0
    total_records_saved: int = 0
    total_duplicates_removed: int = 0
    errors: list[dict] = field(default_factory=list)

    def add_api_call(self, metrics: ApiCallMetrics) -> None:
        """Ajoute les métriques d'un appel API."""
        self.total_api_calls += 1
        if metrics.success:
            self.successful_api_calls += 1
        else:
            self.failed_api_calls += 1
        self.total_records_fetched += metrics.records_count

    def add_error(
        self, error_type: str, message: str, context: dict | None = None
    ) -> None:
        """Ajoute une erreur au rapport."""
        self.errors.append(
            {
                "type": error_type,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context or {},
            }
        )

    def complete(self, records_saved: int = 0, duplicates: int = 0) -> dict:
        """Termine la collecte et retourne le résumé."""
        self.end_time = datetime.now(timezone.utc)
        self.total_records_saved = records_saved
        self.total_duplicates_removed = duplicates

        duration = (self.end_time - self.start_time).total_seconds()

        summary = {
            "extractor": self.extractor_name,
            "duration_seconds": duration,
            "api_calls": {
                "total": self.total_api_calls,
                "successful": self.successful_api_calls,
                "failed": self.failed_api_calls,
                "success_rate": (
                    self.successful_api_calls / self.total_api_calls * 100
                    if self.total_api_calls > 0
                    else 0
                ),
            },
            "records": {
                "fetched": self.total_records_fetched,
                "saved": self.total_records_saved,
                "duplicates_removed": self.total_duplicates_removed,
            },
            "errors_count": len(self.errors),
            "errors": self.errors[:10],  # Limite à 10 erreurs
        }

        logger.info(
            f"Extraction completed | {self.extractor_name} | "
            f"duration={duration:.2f}s | "
            f"api_calls={self.total_api_calls} | "
            f"records_saved={records_saved}"
        )

        return summary


class MetricsCollector:
    """Collecteur de métriques pour un extracteur."""

    def __init__(self, extractor_name: str):
        self.extractor_name = extractor_name
        self.extraction_metrics = ExtractionMetrics(extractor_name=extractor_name)
        self._current_api_call: ApiCallMetrics | None = None

    def start_api_call(self, endpoint: str) -> ApiCallMetrics:
        """Démarre le suivi d'un appel API."""
        self._current_api_call = ApiCallMetrics(endpoint=endpoint)
        return self._current_api_call

    def end_api_call(
        self,
        success: bool = True,
        status_code: int | None = None,
        records_count: int = 0,
        error_message: str | None = None,
    ) -> None:
        """Termine le suivi de l'appel API en cours."""
        if self._current_api_call:
            self._current_api_call.complete(
                success=success,
                status_code=status_code,
                records_count=records_count,
                error_message=error_message,
            )
            self.extraction_metrics.add_api_call(self._current_api_call)
            self._current_api_call = None

    def increment_retry(self) -> None:
        """Incrémente le compteur de retry pour l'appel en cours."""
        if self._current_api_call:
            self._current_api_call.retry_count += 1

    def record_error(
        self, error_type: str, message: str, context: dict | None = None
    ) -> None:
        """Enregistre une erreur."""
        self.extraction_metrics.add_error(error_type, message, context)
        logger.error(f"[{error_type}] {message}")

    def finalize(self, records_saved: int = 0, duplicates: int = 0) -> dict:
        """Finalise la collecte et retourne le résumé."""
        return self.extraction_metrics.complete(records_saved, duplicates)

    def get_summary(self) -> dict:
        """Retourne un résumé des métriques en cours."""
        return {
            "extractor": self.extractor_name,
            "api_calls": self.extraction_metrics.total_api_calls,
            "records_fetched": self.extraction_metrics.total_records_fetched,
            "errors": len(self.extraction_metrics.errors),
        }


def timer(metric_name: str | None = None) -> Callable[[F], F]:
    """Décorateur pour mesurer le temps d'exécution d'une fonction.

    Args:
        metric_name: Nom de la métrique (défaut: nom de la fonction)

    Example:
        @timer("api_call_duration")
        def fetch_data():
            pass
    """

    def decorator(func: F) -> F:
        nonlocal metric_name
        if metric_name is None:
            metric_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.monotonic()
            try:
                result = func(*args, **kwargs)
                duration = (time.monotonic() - start_time) * 1000
                logger.debug(f"[{metric_name}] duration={duration:.2f}ms success=True")
                return result
            except Exception as e:
                duration = (time.monotonic() - start_time) * 1000
                logger.error(f"[{metric_name}] duration={duration:.2f}ms error={e}")
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


class HealthMetrics:
    """Métriques de santé du système."""

    def __init__(self):
        self.checks: dict[str, dict] = {}
        self.last_check_time: datetime | None = None

    def record_check(
        self,
        name: str,
        status: str,
        response_time_ms: float,
        details: dict | None = None,
    ) -> None:
        """Enregistre le résultat d'un health check."""
        self.checks[name] = {
            "status": status,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }
        self.last_check_time = datetime.now(timezone.utc)

    def is_healthy(self) -> bool:
        """Vérifie si tous les checks sont healthy."""
        if not self.checks:
            return False
        return all(check["status"] == "healthy" for check in self.checks.values())

    def get_status(self) -> dict:
        """Retourne le statut global de santé."""
        return {
            "overall_status": "healthy" if self.is_healthy() else "unhealthy",
            "last_check": self.last_check_time.isoformat()
            if self.last_check_time
            else None,
            "checks": self.checks,
        }
