"""Tests d'intégration pour l'extracteur France Travail."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

ft_path = str(Path(__file__).parent.parent.parent / "02_extract" / "france_travail")
sys.path.insert(0, ft_path)

from config import Config  # noqa: E402
from shared.storage import save_ndjson_records  # noqa: E402
from shared.metrics import MetricsCollector  # noqa: E402

# Nettoie sys.path pour éviter les conflits avec les autres modules workspace
sys.path.remove(ft_path)


class TestFranceTravailStorage:
    """Tests d'intégration pour le stockage des données FT."""

    def test_save_offers_to_local_storage(self, mock_local_storage, sample_ft_offers):
        """Test la sauvegarde des offres en mode local."""
        # Crée une config mock
        config = Mock()
        config.storage = "local"
        config.gcs_bucket_name = None

        # Sauvegarde les offres
        save_ndjson_records(
            config=config,
            records=sample_ft_offers,
            destination_name="test_offres.ndjson",
            gcs_prefix="raw_offres",
            local_directory=mock_local_storage,
        )

        # Vérifie que le fichier a été créé
        output_file = Path(mock_local_storage) / "test_offres.ndjson"
        assert output_file.exists()

        # Vérifie le contenu
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2

            # Vérifie que chaque ligne est un JSON valide
            for line in lines:
                record = json.loads(line)
                assert "id" in record
                assert "intitule" in record

    def test_metrics_collection(self, sample_ft_offers):
        """Test la collecte de métriques pendant l'extraction."""
        metrics = MetricsCollector("france_travail")

        # Simule des appels API
        for i in range(3):
            api_metrics = metrics.start_api_call(f"/offres/search?page={i}")
            api_metrics.complete(
                success=True,
                status_code=200,
                records_count=150,
            )
            metrics.end_api_call(
                success=True,
                status_code=200,
                records_count=150,
            )

        # Simule un échec
        api_metrics = metrics.start_api_call("/offres/search?page=3")
        api_metrics.complete(
            success=False,
            status_code=500,
            error_message="Internal Server Error",
        )
        metrics.end_api_call(
            success=False,
            status_code=500,
            error_message="Internal Server Error",
        )

        # Finalise et vérifie
        summary = metrics.finalize(records_saved=450, duplicates=50)

        assert summary["extractor"] == "france_travail"
        assert summary["api_calls"]["total"] == 4
        assert summary["api_calls"]["successful"] == 3
        assert summary["api_calls"]["failed"] == 1
        assert summary["records"]["saved"] == 450
        assert summary["records"]["duplicates_removed"] == 50


class TestFranceTravailConfig:
    """Tests d'intégration pour la configuration FT."""

    def test_config_validation_local_mode(self, mock_local_storage):
        """Test la validation de config en mode local."""
        config = Config(
            project_id="test-project",
            storage="local",
            ft_client_id="test-client-id",
            ft_client_key="test-client-key",
            scope="api_offresdemploiv2",
            gcs_bucket_name="",
            token_url="https://token.example.com",
            offres_base_url="https://api.example.com/offres",
            referentiels_base_url="https://api.example.com/referentiel",
            local_save_dir_offres=mock_local_storage,
            local_save_dir_refs=mock_local_storage,
            search_params=[{"motsCles": "data engineer"}],
        )

        # Ne devrait pas lever d'exception
        config.validate()

        assert config.storage == "local"
        assert config.ft_client_id == "test-client-id"
        assert len(config.search_params) == 1

    def test_config_validation_missing_credentials(self):
        """Test que la validation échoue sans credentials."""
        config = Config(
            project_id="test-project",
            storage="local",
            ft_client_id=None,
            ft_client_key="test-client-key",
            scope="api_offresdemploiv2",
            gcs_bucket_name="",
            token_url="https://token.example.com",
            offres_base_url="https://api.example.com/offres",
            referentiels_base_url="https://api.example.com/referentiel",
            local_save_dir_offres="/tmp",
            local_save_dir_refs="/tmp",
            search_params=[],
        )

        with pytest.raises(ValueError, match="FT_CLIENT_ID"):
            config.validate()


class TestFranceTravailEndToEnd:
    """Tests end-to-end simulés pour France Travail."""

    @pytest.mark.slow
    def test_full_extraction_workflow_mocked(
        self, mock_local_storage, sample_ft_offers
    ):
        """Test le workflow complet avec des mocks."""
        # Évite le conflit avec le module scraper des autres packages workspace
        import sys
        from pathlib import Path

        ft_path = str(
            Path(__file__).parent.parent.parent / "02_extract" / "france_travail"
        )
        sys.path.insert(0, ft_path)
        sys.modules.pop("scraper", None)
        from scraper import OffersExtractor

        sys.path.remove(ft_path)

        # Crée une config mock
        config = Mock()
        config.storage = "local"
        config.gcs_bucket_name = None
        config.local_save_dir_offres = mock_local_storage
        config.offres_base_url = "https://api.example.com/offres"
        config.search_params = [{"motsCles": "data engineer"}]
        config.scope = "api_offresdemploiv2"

        # Mock la session et les réponses
        with patch("scraper.create_authenticated_session") as mock_session:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Range": "0-149/2"}
            mock_response.json.return_value = {"resultats": sample_ft_offers}

            mock_session_instance = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session.return_value = mock_session_instance

            # Exécute l'extraction
            extractor = OffersExtractor(config, mode="test")
            extractor.offers_by_id = {offer["id"]: offer for offer in sample_ft_offers}
            extractor.total_offers_fetched = len(sample_ft_offers)
            extractor._save_results()

            # Vérifie que les fichiers ont été créés
            output_dir = Path(mock_local_storage)
            files = list(output_dir.glob("*.ndjson"))
            assert len(files) == 1

            # Vérifie le contenu
            with open(files[0], "r", encoding="utf-8") as f:
                saved_offers = [json.loads(line) for line in f]
                assert len(saved_offers) == 2
                assert all("id" in offer for offer in saved_offers)
