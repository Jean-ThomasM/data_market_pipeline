import pytest


class TestConfig:
    def test_missing_storage(self):
        from config import Config

        c = Config(
            storage=None,
            project_id=None,
            gcs_bucket_name=None,
            local_save_directory=None,
        )
        with pytest.raises(ValueError, match="STORAGE doit"):
            c.validate()

    def test_gcs_missing_project(self):
        from config import Config

        c = Config(
            storage="gcs",
            project_id=None,
            gcs_bucket_name="b",
            local_save_directory=None,
        )
        with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
            c.validate()

    def test_gcs_missing_bucket(self):
        from config import Config

        c = Config(
            storage="gcs",
            project_id="p",
            gcs_bucket_name=None,
            local_save_directory=None,
        )
        with pytest.raises(ValueError, match="GCS_BUCKET_NAME"):
            c.validate()

    def test_gcs_valid(self):
        from config import Config

        c = Config(
            storage="gcs",
            project_id="p",
            gcs_bucket_name="b",
            local_save_directory=None,
        )
        c.validate()

    def test_local_missing_dir(self):
        from config import Config

        c = Config(
            storage="local",
            project_id=None,
            gcs_bucket_name="",
            local_save_directory=None,
        )
        with pytest.raises(ValueError, match="répertoire local"):
            c.validate()

    def test_local_valid(self):
        from config import Config

        c = Config(
            storage="local",
            project_id=None,
            gcs_bucket_name="",
            local_save_directory="/tmp",
        )
        c.validate()


class TestLoadConfig:
    def test_local(self, mock_env_local):
        from config import load_config

        cfg = load_config()
        assert cfg.storage == "local"
        assert cfg.project_id == "test-project"
        assert cfg.local_save_directory is not None

    def test_gcs(self, mock_env_gcs):
        from config import load_config

        cfg = load_config()
        assert cfg.storage == "gcs"
        assert cfg.project_id == "test-project"
        assert cfg.gcs_bucket_name == "test-bucket"
        assert cfg.local_save_directory is not None

    def test_invalid_storage(self, monkeypatch):
        monkeypatch.setenv("STORAGE", "invalid")
        from config import load_config

        with pytest.raises(ValueError, match="STORAGE doit"):
            load_config()
