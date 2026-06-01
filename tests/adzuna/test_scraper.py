import pytest


class TestBuildSearchLabel:
    def test_with_what(self):
        from scraper import build_search_label

        assert build_search_label({"what": "data+engineer"}) == "data+engineer"

    def test_with_title_only(self):
        from scraper import build_search_label

        assert build_search_label({"title_only": "data"}) == "data"

    def test_fallback(self):
        from scraper import build_search_label

        assert build_search_label({}) == "unknown_search"


class TestRequestWithRetry:
    def test_success(self, mocker, config):
        from scraper import request_with_retry
        import requests

        session = requests.Session()
        resp = mocker.Mock(status_code=200)
        resp.raise_for_status.return_value = None
        mocker.patch.object(session, "get", return_value=resp)

        result = request_with_retry(session, config, "https://api.adzuna.com/search")
        assert result is resp

    def test_429_retry(self, mocker, config):
        from scraper import request_with_retry

        session = type("Session", (), {})()
        retry_resp = mocker.Mock(status_code=429)
        good_resp = mocker.Mock(status_code=200)
        good_resp.raise_for_status.return_value = None

        session.get = mocker.Mock(side_effect=[retry_resp, good_resp])
        mocker.patch("time.sleep")

        result = request_with_retry(session, config, "https://api.adzuna.com/search")
        assert result.status_code == 200

    def test_500_retry(self, mocker, config):
        from scraper import request_with_retry

        session = type("Session", (), {})()
        retry_resp = mocker.Mock(status_code=500)
        good_resp = mocker.Mock(status_code=200)
        good_resp.raise_for_status.return_value = None

        session.get = mocker.Mock(side_effect=[retry_resp, good_resp])
        mocker.patch("time.sleep")

        result = request_with_retry(session, config, "https://api.adzuna.com/search")
        assert result.status_code == 200

    def test_all_attempts_exhausted(self, mocker, config):
        from scraper import request_with_retry

        session = type("Session", (), {})()
        error_resp = mocker.Mock(status_code=429)
        session.get = mocker.Mock(return_value=error_resp)
        mocker.patch("time.sleep")

        with pytest.raises(RuntimeError, match="Request failed after 3 attempts"):
            request_with_retry(session, config, "https://api.adzuna.com/search")


class TestOffersExtractor:
    def test_extract_no_search_params(self, config):
        from scraper import OffersExtractor

        config.search_params = []
        ext = OffersExtractor(config, mode="prod")
        with pytest.raises(ValueError, match="No search parameters"):
            ext.extract()

    def test_deduplication(self, mocker, config):
        from scraper import OffersExtractor

        page_1 = {"count": 3, "results": [{"id": 1}, {"id": 2}]}
        page_2 = {"count": 3, "results": [{"id": 1}, {"id": 3}]}

        mocker.patch.object(
            OffersExtractor, "_fetch_page", side_effect=[page_1, page_2]
        )
        mocker.patch("scraper.time.sleep")
        mocker.patch("scraper.save_ndjson_records")
        config.results_per_page = 2
        config.max_results = 3150

        ext = OffersExtractor(config, mode="prod")
        ext.extract()

        assert "1" in ext.offers_by_id
        assert "2" in ext.offers_by_id
        assert "3" in ext.offers_by_id
        assert len(ext.offers_by_id) == 3

    def test_mode_test_caps_at_200(self, mocker, config):
        from scraper import OffersExtractor

        page_1 = {"count": 5000, "results": [{"id": i} for i in range(50)]}
        subsequent_pages = [
            {
                "count": 5000,
                "results": [{"id": i} for i in range(50 + page * 50, 100 + page * 50)],
            }
            for page in range(5)
        ]

        mocker.patch.object(
            OffersExtractor,
            "_fetch_page",
            side_effect=[page_1] + subsequent_pages,
        )
        mocker.patch("scraper.time.sleep")
        mocker.patch("scraper.save_ndjson_records")

        ext = OffersExtractor(config, mode="test")
        ext.extract()

        assert len(ext.offers_by_id) == 200

    def test_no_offers(self, mocker, config):
        from scraper import OffersExtractor

        mocker.patch.object(
            OffersExtractor,
            "_fetch_page",
            return_value={"count": 0, "results": []},
        )
        mock_save = mocker.patch("scraper.save_ndjson_records")

        ext = OffersExtractor(config, mode="prod")
        ext.extract()

        assert len(ext.offers_by_id) == 0
        mock_save.assert_not_called()

    def test_fewer_results_than_per_page_breaks(self, mocker, config):
        from scraper import OffersExtractor

        page_1 = {"count": 10, "results": [{"id": i} for i in range(10)]}
        mocker.patch.object(OffersExtractor, "_fetch_page", return_value=page_1)
        mocker.patch("scraper.time.sleep")
        mocker.patch("scraper.save_ndjson_records")

        ext = OffersExtractor(config, mode="prod")
        ext.extract()

        assert len(ext.offers_by_id) == 10


class TestExtractOffers:
    def test_extract_offers(self, mocker, config, mock_env_local):
        from scraper import extract_offers, OffersExtractor

        mock_instance = mocker.Mock()
        mocker.patch.object(OffersExtractor, "extract")
        mocker.patch("scraper.OffersExtractor", return_value=mock_instance)
        mocker.patch("scraper.load_config")

        extract_offers(mode="prod")

        mock_instance.extract.assert_called_once()


class TestMain:
    def test_main_prod(self, mocker, monkeypatch, mock_env_local):
        monkeypatch.setenv("ADZUNA_EXTRACT_MODE", "prod")
        mock_extract = mocker.patch("scraper.extract_offers")
        mocker.patch("scraper.load_dotenv")

        from scraper import main

        main()

        mock_extract.assert_called_once_with(mode="prod")

    def test_main_invalid_mode(self, monkeypatch):
        monkeypatch.setenv("ADZUNA_EXTRACT_MODE", "invalid_mode")
        from scraper import main

        with pytest.raises(ValueError, match="ADZUNA_EXTRACT_MODE"):
            main()
