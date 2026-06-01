import pytest


@pytest.fixture
def config():
    from config import Config

    return Config(
        project_id="p",
        storage="local",
        ft_client_id="id",
        ft_client_key="key",
        scope="s",
        gcs_bucket_name="",
        token_url="https://token.example.com",
        offres_base_url="https://api.francetravail.io/offres",
        referentiels_base_url="https://api.francetravail.io/referentiel",
        local_save_dir_offres="/tmp",
        local_save_dir_refs="/tmp",
        search_params=[{"codeROME": "M1811"}],
    )


class TestBuildSearchLabel:
    def test_with_coderome(self):
        from scraper import build_search_label

        assert build_search_label({"codeROME": "M1811"}) == "M1811"

    def test_with_motscles(self):
        from scraper import build_search_label

        assert build_search_label({"motsCles": "data engineer"}) == "data engineer"

    def test_fallback(self):
        from scraper import build_search_label

        assert build_search_label({}) == "unknown_search"


class TestParseTotalResultsCount:
    def test_from_content_range(self):
        import requests
        from scraper import parse_total_results_count

        resp = requests.Response()
        resp.headers["Content-Range"] = "items 0-149/500"
        resp._content = b"{}"

        assert parse_total_results_count(resp) == 500

    def test_fallback_to_json(self, mocker):
        from scraper import parse_total_results_count

        resp = mocker.Mock()
        resp.headers = {}
        resp.json.return_value = {"resultats": [{"id": 1}, {"id": 2}]}

        assert parse_total_results_count(resp) == 2

    def test_fallback_empty(self, mocker):
        from scraper import parse_total_results_count

        resp = mocker.Mock()
        resp.headers = {}
        resp.json.return_value = {}

        assert parse_total_results_count(resp) == 0


class TestRequestWithRetry:
    def test_success(self, mocker, config):
        from scraper import request_with_retry
        import requests

        session = requests.Session()
        resp = mocker.Mock(status_code=200)
        resp.raise_for_status.return_value = None
        mocker.patch.object(session, "get", return_value=resp)

        result = request_with_retry(session, config, "https://example.com")
        assert result is resp

    def test_network_error_then_retry(self, mocker, config):
        from scraper import request_with_retry
        import requests

        session = requests.Session()
        mock_get = mocker.patch.object(session, "get")
        mock_get.side_effect = [
            requests.ConnectionError("conn failed"),
            requests.ConnectionError("conn failed"),
            mocker.Mock(status_code=200),
        ]
        # Make the last one not raise
        mock_get.return_value = mocker.Mock(status_code=200)

        # Redo: side_effect pattern with proper return
        mocker.stopall()
        session2 = requests.Session()
        good_resp = mocker.Mock(status_code=200)
        good_resp.raise_for_status.return_value = None
        mocker.patch.object(
            session2,
            "get",
            side_effect=[requests.ConnectionError("fail"), good_resp],
        )
        mocker.patch("time.sleep")

        result = request_with_retry(session2, config, "https://example.com")
        assert result.status_code == 200

    def test_429_retry(self, mocker, config):
        from scraper import request_with_retry
        import requests

        session = requests.Session()
        good_resp = mocker.Mock(status_code=200)
        good_resp.raise_for_status.return_value = None

        retry_resp = mocker.Mock(status_code=429)
        retry_resp.raise_for_status.side_effect = requests.HTTPError("429")
        # Actually 429 doesn't raise, it continues

        # For 429 the code continues the loop, so no raise_for_status is called
        mocker.patch.object(
            session,
            "get",
            side_effect=[retry_resp, good_resp],
        )
        mocker.patch("time.sleep")

        result = request_with_retry(session, config, "https://example.com")
        assert result.status_code == 200

    def test_401_refresh_token(self, mocker, config):
        from scraper import request_with_retry
        import requests

        session = requests.Session()
        expired_resp = mocker.Mock(status_code=401)
        good_resp = mocker.Mock(status_code=200)
        good_resp.raise_for_status.return_value = None

        mocker.patch.object(session, "get", side_effect=[expired_resp, good_resp])
        mock_refresh = mocker.patch("scraper.refresh_access_token")
        mocker.patch("time.sleep")

        result = request_with_retry(session, config, "https://example.com")
        assert result.status_code == 200
        mock_refresh.assert_called_once()

    def test_204_returns_immediately(self, mocker, config):
        from scraper import request_with_retry
        import requests

        session = requests.Session()
        resp = mocker.Mock(status_code=204)
        mocker.patch.object(session, "get", return_value=resp)

        result = request_with_retry(session, config, "https://example.com")
        assert result.status_code == 204

    def test_all_attempts_exhausted(self, mocker, config):
        from scraper import request_with_retry
        import requests

        session = requests.Session()
        error_resp = mocker.Mock(status_code=429)
        mocker.patch.object(session, "get", return_value=error_resp)
        mocker.patch("time.sleep")

        with pytest.raises(RuntimeError, match="Request failed after 3 attempts"):
            request_with_retry(session, config, "https://example.com")


class TestOffersExtractor:
    @pytest.fixture(autouse=True)
    def _mock_auth_session(self, mocker):
        import requests

        mock_session = mocker.Mock(spec=requests.Session)
        mocker.patch("scraper.create_authenticated_session", return_value=mock_session)

    def test_extract_no_search_params(self, config):
        from scraper import OffersExtractor

        config.search_params = []
        ext = OffersExtractor(config, mode="prod")
        with pytest.raises(ValueError, match="No search parameters"):
            ext.extract()

    def test_extract_204_response(self, mocker, config):
        from scraper import OffersExtractor

        mock_resp = mocker.Mock(status_code=204)
        mocker.patch("scraper.request_with_retry", return_value=mock_resp)

        ext = OffersExtractor(config, mode="prod")
        ext.extract()

        assert ext.unique_offers_added_by_search_label["M1811"] == 0
        assert len(ext.offers_by_id) == 0

    def test_mode_test_caps_at_200(self, mocker, config):
        from scraper import OffersExtractor

        first_page_resp = mocker.Mock(status_code=200)
        first_page_resp.headers = {"Content-Range": "items 0-149/5000"}

        page_0_resp = mocker.Mock(status_code=200)
        page_0_resp.json.return_value = {
            "resultats": [{"id": f"offer-{i}"} for i in range(150)]
        }

        page_1_resp = mocker.Mock(status_code=200)
        page_1_resp.json.return_value = {
            "resultats": [{"id": f"offer-{i}"} for i in range(150, 200)]
        }

        mocker.patch(
            "scraper.request_with_retry",
            side_effect=[first_page_resp, page_0_resp, page_1_resp],
        )
        mocker.patch("scraper.time.sleep")
        mocker.patch("utils.save_ndjson_records")

        ext = OffersExtractor(config, mode="test")
        ext.extract()

        assert len(ext.offers_by_id) == 200

    def test_mode_prod_caps_at_max_results(self, mocker, config):
        from scraper import OffersExtractor, MAX_RESULTS

        first_page_resp = mocker.Mock(status_code=200)
        first_page_resp.headers = {"Content-Range": f"items 0-149/{MAX_RESULTS * 2}"}

        num_pages = MAX_RESULTS // 150 + 1
        page_responses = []
        for p in range(num_pages):
            resp = mocker.Mock(status_code=200)
            base = p * 150
            resp.json.return_value = {
                "resultats": [{"id": f"offer-{base + j}"} for j in range(150)]
            }
            page_responses.append(resp)

        mocker.patch(
            "scraper.request_with_retry",
            side_effect=[first_page_resp] + page_responses,
        )
        mocker.patch("scraper.time.sleep")
        mocker.patch("utils.save_ndjson_records")

        ext = OffersExtractor(config, mode="prod")
        ext.extract()

        assert len(ext.offers_by_id) == MAX_RESULTS

    def test_deduplication(self, mocker, config):
        from scraper import OffersExtractor

        first_page_resp = mocker.Mock(status_code=200)
        first_page_resp.headers = {"Content-Range": "items 0-149/200"}

        page_0_resp = mocker.Mock(status_code=200)
        page_0_resp.json.return_value = {
            "resultats": [{"id": "offer-1"}, {"id": "offer-2"}]
        }

        page_1_resp = mocker.Mock(status_code=200)
        page_1_resp.json.return_value = {
            "resultats": [{"id": "offer-1"}, {"id": "offer-3"}]
        }

        mocker.patch(
            "scraper.request_with_retry",
            side_effect=[first_page_resp, page_0_resp, page_1_resp],
        )
        mocker.patch("scraper.time.sleep")
        mocker.patch("utils.save_ndjson_records")

        ext = OffersExtractor(config, mode="prod")
        ext.extract()

        assert "offer-1" in ext.offers_by_id
        assert "offer-2" in ext.offers_by_id
        assert "offer-3" in ext.offers_by_id
        assert len(ext.offers_by_id) == 3

    def test_no_offers_saves_nothing(self, mocker, config):
        from scraper import OffersExtractor

        mock_save = mocker.patch("utils.save_ndjson_records")
        ext = OffersExtractor(config, mode="prod")
        ext._save_results()

        mock_save.assert_not_called()


class TestReferentialsExtractor:
    def test_extract(self, mocker, config):
        from scraper import ReferentialsExtractor
        from scraper import REFERENTIAL_FILE_NAMES

        mock_resp = mocker.Mock(status_code=200)
        mock_resp.json.return_value = [{"code": "M1811"}]

        mocker.patch("scraper.request_with_retry", return_value=mock_resp)
        mocker.patch("scraper.create_authenticated_session")
        mock_save = mocker.patch("utils.save_json_payload")
        mocker.patch("scraper.time.sleep")

        ext = ReferentialsExtractor(config)
        ext.extract()

        for endpoint, filename in REFERENTIAL_FILE_NAMES.items():
            mock_save.assert_any_call(
                config=config,
                payload=[{"code": "M1811"}],
                destination_name=filename,
                gcs_prefix="raw_referentiels",
                local_directory=config.local_save_dir_refs,
            )
