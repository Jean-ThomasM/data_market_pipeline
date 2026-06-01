import pytest


@pytest.fixture
def config():
    from config import Config

    return Config(
        storage="local",
        project_id=None,
        gcs_bucket_name="",
        local_save_directory="/tmp",
    )


class TestGeoExtractor:
    def test_fetch_resource_success(self, mocker, config):
        from scraper import GeoExtractor

        mock_resp = mocker.Mock()
        mock_resp.json.return_value = [{"code": "01", "nom": "Test"}]
        mock_session = mocker.Mock()
        mock_session.get.return_value = mock_resp

        ext = GeoExtractor(config)
        ext.session = mock_session
        result = ext._fetch_resource("regions")

        assert result == [{"code": "01", "nom": "Test"}]
        mock_session.get.assert_called_once_with(
            "https://geo.api.gouv.fr/regions", timeout=30
        )

    def test_fetch_resource_http_error(self, mocker, config):
        import requests
        from scraper import GeoExtractor

        mock_session = mocker.Mock()
        mock_session.get.side_effect = requests.RequestException("API error")

        ext = GeoExtractor(config)
        ext.session = mock_session
        with pytest.raises(RuntimeError, match="Erreur API GEO"):
            ext._fetch_resource("regions")

    def test_fetch_resource_invalid_payload(self, mocker, config):
        from scraper import GeoExtractor

        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"not": "a list"}
        mock_session = mocker.Mock()
        mock_session.get.return_value = mock_resp

        ext = GeoExtractor(config)
        ext.session = mock_session
        with pytest.raises(RuntimeError, match="Réponse inattendue"):
            ext._fetch_resource("regions")

    def test_extract_calls_all_resources(self, mocker, config):
        from scraper import GeoExtractor, RESOURCE_PATHS, RESOURCE_FILE_NAMES

        ext = GeoExtractor(config)
        mock_fetch = mocker.patch.object(
            ext, "_fetch_resource", return_value=[{"id": 1}]
        )
        mock_save = mocker.patch("utils.save_ndjson_records")

        ext.extract()

        for resource_name in RESOURCE_PATHS:
            mock_fetch.assert_any_call(resource_name)
            mock_save.assert_any_call(
                config=config,
                records=[{"id": 1}],
                destination_name=RESOURCE_FILE_NAMES[resource_name],
                gcs_prefix="raw_geo",
                local_directory=config.local_save_directory,
            )
        assert mock_fetch.call_count == len(RESOURCE_PATHS)


class TestExtractGeo:
    def test_extract_geo(self, mocker, mock_env_local):
        from scraper import extract_geo, GeoExtractor

        mock_ext = mocker.Mock()
        mocker.patch.object(GeoExtractor, "extract")
        mocker.patch("scraper.GeoExtractor", return_value=mock_ext)
        mocker.patch("scraper.load_config")

        extract_geo()

        mock_ext.extract.assert_called_once()
