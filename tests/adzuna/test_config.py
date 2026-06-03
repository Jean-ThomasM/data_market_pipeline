import pytest


class TestConfigValidate:
    def test_missing_storage(self):
        from config import Config

        c = Config(
            project_id=None,
            storage=None,
            adzuna_app_id="id",
            adzuna_app_key="key",
            gcs_bucket_name="",
            jobs_base_url="",
            country="fr",
            local_save_dir_offres=None,
            search_params=[{"what": "test"}],
            results_per_page=50,
            max_results=3150,
            request_delay_seconds=1.0,
            request_timeout_seconds=30,
            sort_by=None,
        )
        with pytest.raises(ValueError, match="STORAGE doit"):
            c.validate()

    def test_gcs_missing_project(self):
        from config import Config

        c = Config(
            project_id=None,
            storage="gcs",
            adzuna_app_id="id",
            adzuna_app_key="key",
            gcs_bucket_name="bucket",
            jobs_base_url="",
            country="fr",
            local_save_dir_offres=None,
            search_params=[{"what": "test"}],
            results_per_page=50,
            max_results=3150,
            request_delay_seconds=1.0,
            request_timeout_seconds=30,
            sort_by=None,
        )
        with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
            c.validate()

    def test_gcs_missing_bucket(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="gcs",
            adzuna_app_id="id",
            adzuna_app_key="key",
            gcs_bucket_name=None,
            jobs_base_url="",
            country="fr",
            local_save_dir_offres=None,
            search_params=[{"what": "test"}],
            results_per_page=50,
            max_results=3150,
            request_delay_seconds=1.0,
            request_timeout_seconds=30,
            sort_by=None,
        )
        with pytest.raises(ValueError, match="GCS_BUCKET_NAME"):
            c.validate()

    def test_missing_app_id(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="local",
            adzuna_app_id=None,
            adzuna_app_key="key",
            gcs_bucket_name="",
            jobs_base_url="",
            country="fr",
            local_save_dir_offres="/tmp",
            search_params=[{"what": "test"}],
            results_per_page=50,
            max_results=3150,
            request_delay_seconds=1.0,
            request_timeout_seconds=30,
            sort_by=None,
        )
        with pytest.raises(ValueError, match="ADZUNA_API_ID"):
            c.validate()

    def test_missing_app_key(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="local",
            adzuna_app_id="id",
            adzuna_app_key=None,
            gcs_bucket_name="",
            jobs_base_url="",
            country="fr",
            local_save_dir_offres="/tmp",
            search_params=[{"what": "test"}],
            results_per_page=50,
            max_results=3150,
            request_delay_seconds=1.0,
            request_timeout_seconds=30,
            sort_by=None,
        )
        with pytest.raises(ValueError, match="ADZUNA_API_KEY"):
            c.validate()

    def test_no_search_params(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="local",
            adzuna_app_id="id",
            adzuna_app_key="key",
            gcs_bucket_name="",
            jobs_base_url="",
            country="fr",
            local_save_dir_offres="/tmp",
            search_params=[],
            results_per_page=50,
            max_results=3150,
            request_delay_seconds=1.0,
            request_timeout_seconds=30,
            sort_by=None,
        )
        with pytest.raises(ValueError, match="Aucun paramètre de recherche"):
            c.validate()

    def test_results_per_page_out_of_range(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="local",
            adzuna_app_id="id",
            adzuna_app_key="key",
            gcs_bucket_name="",
            jobs_base_url="",
            country="fr",
            local_save_dir_offres="/tmp",
            search_params=[{"what": "test"}],
            results_per_page=0,
            max_results=3150,
            request_delay_seconds=1.0,
            request_timeout_seconds=30,
            sort_by=None,
        )
        with pytest.raises(ValueError, match="ADZUNA_RESULTS_PER_PAGE"):
            c.validate()

    def test_valid(self):
        from config import Config

        c = Config(
            project_id="p",
            storage="local",
            adzuna_app_id="id",
            adzuna_app_key="key",
            gcs_bucket_name="",
            jobs_base_url="",
            country="fr",
            local_save_dir_offres="/tmp",
            search_params=[{"what": "test"}],
            results_per_page=50,
            max_results=3150,
            request_delay_seconds=1.0,
            request_timeout_seconds=30,
            sort_by=None,
        )
        c.validate()


class TestNormalizeSearchParams:
    def test_empty(self):
        from config import _normalize_search_params

        assert _normalize_search_params(None) == [{"what": "data+engineer"}]
        assert _normalize_search_params([]) == [{"what": "data+engineer"}]

    def test_string_params(self):
        from config import _normalize_search_params

        result = _normalize_search_params(["data+scientist", "dev+ops"])
        assert result == [{"what": "data+scientist"}, {"what": "dev+ops"}]

    def test_dict_params(self):
        from config import _normalize_search_params

        result = _normalize_search_params([{"what": "data+engineer", "category": "it"}])
        assert result == [{"what": "data+engineer", "category": "it"}]

    def test_invalid(self):
        from config import _normalize_search_params

        with pytest.raises(ValueError, match="paramètres de recherche"):
            _normalize_search_params([42])


class TestLoadConfig:
    def test_local(self, mock_env_local):
        from config import load_config

        cfg = load_config()
        assert cfg.storage == "local"
        assert cfg.adzuna_app_id == "test-app-id"
        assert cfg.adzuna_app_key == "test-app-key"
        assert cfg.country == "fr"
        assert cfg.sort_by == "date"
        assert cfg.results_per_page == 50

    def test_invalid_storage(self, monkeypatch):
        monkeypatch.setenv("STORAGE", "invalid")
        from config import load_config

        with pytest.raises(ValueError, match="STORAGE doit"):
            load_config()
