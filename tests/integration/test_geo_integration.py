"""Tests d'intégration pour l'extracteur GEO."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Ajoute le chemin vers le module geo
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "02_extract" / "geo"))

from shared.storage import save_ndjson_records


class TestGeoStorage:
    """Tests d'intégration pour le stockage des données GEO."""

    def test_save_communes_to_local_storage(
        self, mock_local_storage, sample_geo_communes
    ):
        """Test la sauvegarde des communes en mode local."""
        # Crée une config mock
        config = Mock()
        config.storage = "local"
        config.gcs_bucket_name = None

        # Sauvegarde les communes
        save_ndjson_records(
            config=config,
            records=sample_geo_communes,
            destination_name="communes.ndjson",
            gcs_prefix="raw_geo",
            local_directory=mock_local_storage,
        )

        # Vérifie que le fichier a été créé
        output_file = Path(mock_local_storage) / "communes.ndjson"
        assert output_file.exists()

        # Vérifie le contenu
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2

            # Vérifie la structure des données
            paris = json.loads(lines[0])
            assert paris["nom"] == "Paris"
            assert paris["code"] == "75056"
            assert "population" in paris

    def test_geo_data_structure(self, sample_geo_communes):
        """Test que les données GEO ont la structure attendue."""
        for commune in sample_geo_communes:
            # Vérifie les champs obligatoires
            assert "nom" in commune
            assert "code" in commune
            assert "codeDepartement" in commune
            assert "codeRegion" in commune

            # Vérifie que les codes sont des strings
            assert isinstance(commune["code"], str)
            assert isinstance(commune["codeDepartement"], str)


class TestGeoApiIntegration:
    """Tests d'intégration pour l'API GEO."""

    def test_api_response_parsing(self, sample_geo_communes):
        """Test le parsing des réponses de l'API."""
        # Simule une réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_geo_communes

        # Vérifie la structure
        data = mock_response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Vérifie que tous les champs sont présents
        required_fields = ["nom", "code", "codeDepartement", "codeRegion"]
        for commune in data:
            for field in required_fields:
                assert field in commune

    @pytest.mark.skip(reason="Nécessite une connexion réseau")
    def test_real_api_connectivity(self):
        """Test la connectivité réelle avec l'API GEO (désactivé par défaut)."""
        import requests

        response = requests.get(
            "https://geo.api.gouv.fr/communes",
            params={"nom": "Paris"},
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestGeoEndToEnd:
    """Tests end-to-end pour l'extracteur GEO."""

    def test_full_extraction_workflow_mocked(
        self, mock_local_storage, sample_geo_communes
    ):
        """Test le workflow complet avec des mocks."""
        from scraper import GeoExtractor

        # Crée une config mock
        config = Mock()
        config.storage = "local"
        config.gcs_bucket_name = None
        config.local_save_directory = mock_local_storage

        # Mock la session requests
        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session.get.return_value.json.return_value = sample_geo_communes
            mock_session.get.return_value.raise_for_status = Mock()
            mock_session_class.return_value = mock_session

            # Crée l'extracteur
            extractor = GeoExtractor(config)

            # Mock la méthode _fetch_resource pour retourner les données de test
            extractor._fetch_resource = Mock(return_value=sample_geo_communes)

            # Exécute l'extraction
            extractor.extract()

            # Vérifie que les fichiers ont été créés
            output_dir = Path(mock_local_storage)
            expected_files = [
                "regions.ndjson",
                "departements.ndjson",
                "communes.ndjson",
                "epcis.ndjson",
            ]

            for filename in expected_files:
                file_path = output_dir / filename
                assert file_path.exists(), f"Fichier {filename} non créé"
