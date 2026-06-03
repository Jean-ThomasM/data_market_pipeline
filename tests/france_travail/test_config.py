import pytest


class TestConfigValidate:
    def test_missing_project_id(self):
        from config import Config

        c = Config(
            project_id=None,
            storage="local",
            ft_client_id="id",
            ft_client_key="key",
            scope="s",
            gcs_bucket_name="",
            token_url="",
            offres_base_url="",
            referentiels_base_url="",
            local_save_dir_offres="/tmp",
            local_save_dir_refs="/tmp",
            search_params=[],
        )
        with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
            c.validate()

    def test_missing_client_id(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="local",
            ft_client_id=None,
            ft_client_key="key",
            scope="s",
            gcs_bucket_name="",
            token_url="",
            offres_base_url="",
            referentiels_base_url="",
            local_save_dir_offres="/tmp",
            local_save_dir_refs="/tmp",
            search_params=[],
        )
        with pytest.raises(ValueError, match="FT_CLIENT_ID"):
            c.validate()

    def test_missing_client_key(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="local",
            ft_client_id="id",
            ft_client_key=None,
            scope="s",
            gcs_bucket_name="",
            token_url="",
            offres_base_url="",
            referentiels_base_url="",
            local_save_dir_offres="/tmp",
            local_save_dir_refs="/tmp",
            search_params=[],
        )
        with pytest.raises(ValueError, match="FT_CLIENT_KEY"):
            c.validate()

    def test_valid(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="local",
            ft_client_id="id",
            ft_client_key="key",
            scope="s",
            gcs_bucket_name="",
            token_url="",
            offres_base_url="",
            referentiels_base_url="",
            local_save_dir_offres="/tmp",
            local_save_dir_refs="/tmp",
            search_params=[],
        )
        c.validate()


class TestBuildDefaultSearchParams:
    def test_returns_list(self, monkeypatch):
        from config import build_default_search_params

        result = build_default_search_params()
        assert isinstance(result, list)
        assert len(result) >= 1
        for item in result:
            assert isinstance(item, dict)

    def test_default_rome_code(self, monkeypatch):
        monkeypatch.delenv("FT_ROME_CODE", raising=False)
        from config import build_default_search_params

        result = build_default_search_params()
        assert result[0]["codeROME"] == "M1811"

    def test_custom_rome_code(self, monkeypatch):
        monkeypatch.setenv("FT_ROME_CODE", "M1812")
        from config import build_default_search_params

        result = build_default_search_params()
        assert result[0]["codeROME"] == "M1812"


class TestLoadConfig:
    def test_local(self, mock_env_local):
        from config import load_config

        cfg = load_config()
        assert cfg.storage == "local"
        assert cfg.project_id == "test-project"
        assert cfg.ft_client_id == "test-client-id"
        assert cfg.ft_client_key == "test-client-key"
        assert cfg.scope == "api_offresdemploiv2 o2dsoffre"
        assert cfg.local_save_dir_offres is not None
        assert cfg.local_save_dir_refs is not None
        assert len(cfg.search_params) > 0

    def test_invalid_storage(self, monkeypatch):
        monkeypatch.setenv("STORAGE", "invalid")
        from config import load_config

        with pytest.raises(ValueError, match="STORAGE doit"):
            load_config()
