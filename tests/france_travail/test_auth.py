import pytest


@pytest.fixture
def config():
    from config import Config

    return Config(
        project_id="p",
        storage="local",
        ft_client_id="client-id",
        ft_client_key="client-key",
        scope="api_offresdemploiv2",
        gcs_bucket_name="",
        token_url="https://token.example.com",
        offres_base_url="https://api.example.com/offres",
        referentiels_base_url="https://api.example.com/referentiel",
        local_save_dir_offres="/tmp",
        local_save_dir_refs="/tmp",
        search_params=[],
    )


class TestGetToken:
    def test_success(self, mocker, config):
        from auth import get_token

        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"access_token": "abc123"}
        mocker.patch("requests.post", return_value=mock_resp)

        token = get_token(config)
        assert token == "abc123"

    def test_http_error(self, mocker, config):
        import requests
        from auth import get_token

        mock_resp = mocker.Mock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("401")
        mocker.patch("requests.post", return_value=mock_resp)

        with pytest.raises(requests.HTTPError):
            get_token(config)

    def test_empty_token(self, mocker, config):
        from auth import get_token

        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {}
        mocker.patch("requests.post", return_value=mock_resp)

        with pytest.raises(ValueError, match="token vide"):
            get_token(config)


class TestCreateAuthenticatedSession:
    def test_sets_auth_header(self, mocker, config):
        from auth import create_authenticated_session

        mocker.patch("auth.get_token", return_value="test-token")
        session = create_authenticated_session(config)

        assert session.headers["Authorization"] == "Bearer test-token"


class TestRefreshAccessToken:
    def test_updates_header(self, mocker, config):
        from auth import refresh_access_token
        import requests

        mocker.patch("auth.get_token", return_value="new-token")
        session = requests.Session()
        session.headers.update({"Authorization": "Bearer old-token"})

        refresh_access_token(session, config)
        assert session.headers["Authorization"] == "Bearer new-token"
