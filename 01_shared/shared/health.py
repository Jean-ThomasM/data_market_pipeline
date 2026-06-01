"""Module de health checks pour les extracteurs et services."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import requests

from shared.logging_config import get_logger

logger = get_logger("health")


class HealthStatus(Enum):
    """Statut de santé d'un composant."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Résultat d'un health check."""

    name: str
    status: HealthStatus
    response_time_ms: float
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convertit le résultat en dictionnaire."""
        return {
            "name": self.name,
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class HealthCheck(ABC):
    """Classe de base pour les health checks."""

    def __init__(self, name: str, timeout_seconds: float = 5.0):
        self.name = name
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def check(self) -> HealthCheckResult:
        """Exécute le health check.

        Returns:
            HealthCheckResult avec le statut du check
        """
        pass


class ApiHealthCheck(HealthCheck):
    """Health check pour une API HTTP."""

    def __init__(
        self,
        name: str,
        url: str,
        expected_status: int = 200,
        timeout_seconds: float = 5.0,
        headers: dict | None = None,
    ):
        super().__init__(name, timeout_seconds)
        self.url = url
        self.expected_status = expected_status
        self.headers = headers or {}

    def check(self) -> HealthCheckResult:
        """Vérifie la disponibilité de l'API."""
        start_time = time.monotonic()

        try:
            response = requests.get(
                self.url,
                headers=self.headers,
                timeout=self.timeout_seconds,
            )
            response_time = (time.monotonic() - start_time) * 1000

            if response.status_code == self.expected_status:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message=f"API responded with {response.status_code}",
                    metadata={
                        "url": self.url,
                        "status_code": response.status_code,
                    },
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message=f"Unexpected status code: {response.status_code}",
                    metadata={
                        "url": self.url,
                        "expected_status": self.expected_status,
                        "actual_status": response.status_code,
                    },
                )

        except requests.Timeout:
            response_time = (time.monotonic() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Request timed out after {self.timeout_seconds}s",
                metadata={"url": self.url, "timeout": self.timeout_seconds},
            )

        except requests.RequestException as e:
            response_time = (time.monotonic() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Request failed: {str(e)}",
                metadata={"url": self.url, "error": str(e)},
            )


class GcsHealthCheck(HealthCheck):
    """Health check pour Google Cloud Storage."""

    def __init__(
        self,
        name: str = "gcs",
        bucket_name: str | None = None,
        timeout_seconds: float = 10.0,
    ):
        super().__init__(name, timeout_seconds)
        self.bucket_name = bucket_name

    def check(self) -> HealthCheckResult:
        """Vérifie la connectivité GCS."""
        start_time = time.monotonic()

        try:
            from google.cloud import storage
            from google.api_core.exceptions import NotFound

            client = storage.Client()

            if self.bucket_name:
                # Vérifie un bucket spécifique
                try:
                    bucket = client.bucket(self.bucket_name)
                    bucket.reload(timeout=self.timeout_seconds)
                    response_time = (time.monotonic() - start_time) * 1000

                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        message=f"GCS bucket '{self.bucket_name}' accessible",
                        metadata={"bucket": self.bucket_name},
                    )
                except NotFound:
                    response_time = (time.monotonic() - start_time) * 1000
                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message=f"GCS bucket '{self.bucket_name}' not found",
                        metadata={"bucket": self.bucket_name},
                    )
            else:
                # Liste les buckets pour vérifier la connectivité
                list(client.list_buckets(max_results=1))
                response_time = (time.monotonic() - start_time) * 1000

                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="GCS connectivity OK",
                )

        except Exception as e:
            response_time = (time.monotonic() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"GCS check failed: {str(e)}",
                metadata={"error": str(e)},
            )


class BigQueryHealthCheck(HealthCheck):
    """Health check pour BigQuery."""

    def __init__(
        self,
        name: str = "bigquery",
        project_id: str | None = None,
        timeout_seconds: float = 10.0,
    ):
        super().__init__(name, timeout_seconds)
        self.project_id = project_id

    def check(self) -> HealthCheckResult:
        """Vérifie la connectivité BigQuery."""
        start_time = time.monotonic()

        try:
            from google.cloud import bigquery

            client = bigquery.Client(project=self.project_id)

            # Exécute une requête simple
            query = "SELECT 1 as health_check"
            job = client.query(query, timeout=self.timeout_seconds)
            result = list(job.result())

            response_time = (time.monotonic() - start_time) * 1000

            if result and result[0][0] == 1:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="BigQuery connectivity OK",
                    metadata={"project_id": self.project_id},
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    message="BigQuery query returned unexpected result",
                )

        except Exception as e:
            response_time = (time.monotonic() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"BigQuery check failed: {str(e)}",
                metadata={"error": str(e)},
            )


class SecretManagerHealthCheck(HealthCheck):
    """Health check pour Secret Manager."""

    def __init__(
        self,
        name: str = "secret_manager",
        project_id: str | None = None,
        timeout_seconds: float = 5.0,
    ):
        super().__init__(name, timeout_seconds)
        self.project_id = project_id

    def check(self) -> HealthCheckResult:
        """Vérifie la connectivité Secret Manager."""
        start_time = time.monotonic()

        try:
            from google.cloud import secretmanager

            client = secretmanager.SecretManagerServiceClient()

            # Liste les secrets (sans les valeurs) pour vérifier la connectivité
            if self.project_id:
                parent = f"projects/{self.project_id}"
                list(
                    client.list_secrets(
                        request={"parent": parent}, timeout=self.timeout_seconds
                    )
                )

            response_time = (time.monotonic() - start_time) * 1000

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                message="Secret Manager connectivity OK",
                metadata={"project_id": self.project_id},
            )

        except Exception as e:
            response_time = (time.monotonic() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Secret Manager check failed: {str(e)}",
                metadata={"error": str(e)},
            )


class HealthCheckRegistry:
    """Registre de health checks."""

    def __init__(self):
        self.checks: list[HealthCheck] = []

    def register(self, check: HealthCheck) -> None:
        """Enregistre un health check."""
        self.checks.append(check)
        logger.debug(f"Registered health check: {check.name}")

    def unregister(self, name: str) -> None:
        """Supprime un health check."""
        self.checks = [c for c in self.checks if c.name != name]

    def run_all(self) -> dict:
        """Exécute tous les health checks.

        Returns:
            Dictionnaire avec le statut global et les résultats
        """
        results = []
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0

        for check in self.checks:
            try:
                result = check.check()
                results.append(result.to_dict())

                if result.status == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif result.status == HealthStatus.DEGRADED:
                    degraded_count += 1
                else:
                    unhealthy_count += 1

            except Exception as e:
                logger.error(f"Health check {check.name} failed with exception: {e}")
                results.append(
                    {
                        "name": check.name,
                        "status": HealthStatus.UNHEALTHY.value,
                        "message": f"Check failed with exception: {str(e)}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                unhealthy_count += 1

        # Détermine le statut global
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        elif healthy_count > 0:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN

        return {
            "status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": len(self.checks),
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
            },
            "checks": results,
        }

    def is_healthy(self) -> bool:
        """Vérifie si tous les checks sont healthy."""
        result = self.run_all()
        return result["status"] == HealthStatus.HEALTHY.value


def create_default_health_checks(
    project_id: str | None = None,
    gcs_bucket: str | None = None,
) -> HealthCheckRegistry:
    """Crée un registre avec les health checks par défaut pour GCP.

    Args:
        project_id: ID du projet GCP
        gcs_bucket: Nom du bucket GCS à vérifier

    Returns:
        HealthCheckRegistry configuré
    """
    registry = HealthCheckRegistry()

    # Ajoute les checks GCP si on est en mode cloud
    if project_id:
        registry.register(GcsHealthCheck(bucket_name=gcs_bucket))
        registry.register(BigQueryHealthCheck(project_id=project_id))
        registry.register(SecretManagerHealthCheck(project_id=project_id))

    return registry
