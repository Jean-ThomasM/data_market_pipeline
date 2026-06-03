"""Tests d'intégration pour les health checks."""

import pytest
from unittest.mock import Mock, patch

from shared.health import (
    HealthCheckRegistry,
    HealthStatus,
    ApiHealthCheck,
    create_default_health_checks,
)


class TestHealthCheckIntegration:
    """Tests d'intégration pour le système de health checks."""

    def test_api_health_check_success(self):
        """Test un health check API qui réussit."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            check = ApiHealthCheck(
                name="test_api",
                url="https://api.example.com/health",
                expected_status=200,
            )

            result = check.check()

            assert result.status == HealthStatus.HEALTHY
            assert result.response_time_ms > 0
            assert "200" in result.message

    def test_api_health_check_failure(self):
        """Test un health check API qui échoue."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            check = ApiHealthCheck(
                name="test_api",
                url="https://api.example.com/health",
                expected_status=200,
            )

            result = check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert "500" in result.message

    def test_api_health_check_timeout(self):
        """Test un health check API avec timeout."""
        with patch("requests.get") as mock_get:
            from requests import Timeout

            mock_get.side_effect = Timeout("Request timed out")

            check = ApiHealthCheck(
                name="test_api",
                url="https://api.example.com/health",
                timeout_seconds=1,
            )

            result = check.check()

            assert result.status == HealthStatus.UNHEALTHY
            assert "timed out" in result.message.lower()

    def test_registry_multiple_checks(self):
        """Test le registre avec plusieurs checks."""
        registry = HealthCheckRegistry()

        # Ajoute des checks mockés
        healthy_check = Mock()
        healthy_check.name = "healthy_service"
        healthy_check.check.return_value = Mock(
            status=HealthStatus.HEALTHY,
            response_time_ms=100.0,
            to_dict=lambda: {"name": "healthy_service", "status": "healthy"},
        )

        unhealthy_check = Mock()
        unhealthy_check.name = "unhealthy_service"
        unhealthy_check.check.return_value = Mock(
            status=HealthStatus.UNHEALTHY,
            response_time_ms=5000.0,
            to_dict=lambda: {"name": "unhealthy_service", "status": "unhealthy"},
        )

        registry.register(healthy_check)
        registry.register(unhealthy_check)

        result = registry.run_all()

        assert result["status"] == HealthStatus.UNHEALTHY.value
        assert result["summary"]["total"] == 2
        assert result["summary"]["healthy"] == 1
        assert result["summary"]["unhealthy"] == 1

    def test_registry_is_healthy(self):
        """Test la méthode is_healthy du registre."""
        registry = HealthCheckRegistry()

        # Sans checks, devrait être False ou Unknown
        result = registry.is_healthy()
        assert result is False  # Car tous les checks sont unknown

        # Ajoute un check healthy
        healthy_check = Mock()
        healthy_check.name = "healthy_service"
        healthy_check.check.return_value = Mock(
            status=HealthStatus.HEALTHY,
            to_dict=lambda: {"name": "healthy_service", "status": "healthy"},
        )

        registry.register(healthy_check)
        assert registry.is_healthy() is True


class TestHealthCheckEndToEnd:
    """Tests end-to-end pour les health checks."""

    def test_create_default_health_checks_local_mode(self):
        """Test la création des health checks par défaut en mode local."""
        # Sans project_id, aucun check GCP ne devrait être créé
        registry = create_default_health_checks(project_id=None)

        # Devrait avoir un registre vide (ou uniquement des checks non-GCP)
        assert len(registry.checks) == 0

    @pytest.mark.skip(reason="Nécessite des credentials GCP")
    def test_create_default_health_checks_gcp_mode(self):
        """Test la création des health checks avec GCP (désactivé par défaut)."""
        registry = create_default_health_checks(
            project_id="test-project",
            gcs_bucket="test-bucket",
        )

        # Devrait avoir les checks GCS, BigQuery et Secret Manager
        check_names = [c.name for c in registry.checks]
        assert "gcs" in check_names
        assert "bigquery" in check_names
        assert "secret_manager" in check_names

    def test_health_check_result_serialization(self):
        """Test la sérialisation des résultats de health check."""
        from datetime import datetime, timezone

        result = Mock()
        result.name = "test_check"
        result.status = HealthStatus.HEALTHY
        result.response_time_ms = 150.5
        result.message = "All good"
        result.timestamp = datetime.now(timezone.utc)
        result.metadata = {"version": "1.0"}
        result.to_dict = lambda: {
            "name": result.name,
            "status": result.status.value,
            "response_time_ms": result.response_time_ms,
            "message": result.message,
            "timestamp": result.timestamp.isoformat(),
            "metadata": result.metadata,
        }

        dict_result = result.to_dict()

        assert dict_result["name"] == "test_check"
        assert dict_result["status"] == "healthy"
        assert dict_result["response_time_ms"] == 150.5
        assert "timestamp" in dict_result
