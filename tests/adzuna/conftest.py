import os
import sys
import pytest

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
MY_SRC = os.path.join(PROJECT_ROOT, "02_extract", "adzuna")


@pytest.fixture(autouse=True)
def _isolate_imports():
    old_path = list(sys.path)
    old_modules = {}
    for k, v in list(sys.modules.items()):
        f = getattr(v, "__file__", None)
        if f and "02_extract" in os.path.normpath(f):
            old_modules[k] = sys.modules.pop(k)
    for p in list(sys.path):
        normalized = os.path.normpath(p) if p else PROJECT_ROOT
        if normalized == PROJECT_ROOT:
            sys.path.remove(p)
        elif "02_extract" in normalized and normalized != MY_SRC:
            sys.path.remove(p)
    if MY_SRC not in sys.path:
        sys.path.insert(0, MY_SRC)
    yield
    sys.path[:] = old_path
    sys.modules.update(old_modules)


@pytest.fixture
def mock_env_local(monkeypatch):
    monkeypatch.setenv("STORAGE", "local")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("GCS_BUCKET_NAME", "")
    monkeypatch.setenv("ADZUNA_API_ID", "test-app-id")
    monkeypatch.setenv("ADZUNA_API_KEY", "test-app-key")


@pytest.fixture
def config():
    from config import Config

    return Config(
        project_id="p",
        storage="local",
        adzuna_app_id="app-id",
        adzuna_app_key="app-key",
        gcs_bucket_name="",
        jobs_base_url="https://api.adzuna.com/v1/api/jobs",
        country="fr",
        local_save_dir_offres="/tmp",
        search_params=[{"what": "data+engineer"}],
        results_per_page=50,
        max_results=3150,
        request_delay_seconds=1.0,
        request_timeout_seconds=30,
        sort_by="date",
    )
