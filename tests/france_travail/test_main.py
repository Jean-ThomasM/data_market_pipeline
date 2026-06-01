import pytest


class TestGetExtractTarget:
    @pytest.fixture(autouse=True)
    def _mock_env_for_import(self, monkeypatch):
        monkeypatch.setenv("STORAGE", "local")
        monkeypatch.setenv("GCP_PROJECT_ID", "test")
        monkeypatch.setenv("FT_CLIENT_ID", "test")
        monkeypatch.setenv("FT_CLIENT_KEY", "test")

    def test_default(self, monkeypatch):
        monkeypatch.delenv("FT_EXTRACT_TARGET", raising=False)
        from main import _get_extract_target

        assert _get_extract_target() == "offers"

    def test_offers(self, monkeypatch):
        monkeypatch.setenv("FT_EXTRACT_TARGET", "offers")
        from main import _get_extract_target

        assert _get_extract_target() == "offers"

    def test_referentials(self, monkeypatch):
        monkeypatch.setenv("FT_EXTRACT_TARGET", "referentials")
        from main import _get_extract_target

        assert _get_extract_target() == "referentials"

    def test_referentiels_alias(self, monkeypatch):
        monkeypatch.setenv("FT_EXTRACT_TARGET", "referentiels")
        from main import _get_extract_target

        assert _get_extract_target() == "referentials"

    def test_all(self, monkeypatch):
        monkeypatch.setenv("FT_EXTRACT_TARGET", "all")
        from main import _get_extract_target

        assert _get_extract_target() == "all"

    def test_invalid(self, monkeypatch):
        monkeypatch.setenv("FT_EXTRACT_TARGET", "invalid")
        from main import _get_extract_target

        with pytest.raises(ValueError, match="FT_EXTRACT_TARGET invalide"):
            _get_extract_target()


class TestMain:
    def test_offers(self, mocker, monkeypatch, mock_env_local):
        monkeypatch.setenv("FT_EXTRACT_TARGET", "offers")
        mock_extract_offers = mocker.patch("main.extract_offers")
        mock_extract_refs = mocker.patch("main.extract_referentials")
        mocker.patch("main.load_dotenv")

        from main import main

        main()

        mock_extract_offers.assert_called_once_with(mode="prod")
        mock_extract_refs.assert_not_called()

    def test_referentials(self, mocker, monkeypatch, mock_env_local):
        monkeypatch.setenv("FT_EXTRACT_TARGET", "referentials")
        mock_extract_offers = mocker.patch("main.extract_offers")
        mock_extract_refs = mocker.patch("main.extract_referentials")
        mocker.patch("main.load_dotenv")

        from main import main

        main()

        mock_extract_refs.assert_called_once()
        mock_extract_offers.assert_not_called()

    def test_all(self, mocker, monkeypatch, mock_env_local):
        monkeypatch.setenv("FT_EXTRACT_TARGET", "all")
        mock_extract_offers = mocker.patch("main.extract_offers")
        mock_extract_refs = mocker.patch("main.extract_referentials")
        mocker.patch("main.load_dotenv")

        from main import main

        main()

        mock_extract_refs.assert_called_once()
        mock_extract_offers.assert_called_once_with(mode="prod")
