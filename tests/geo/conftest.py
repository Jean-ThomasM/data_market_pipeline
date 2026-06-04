import os
import sys
import pytest

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
MY_SRC = os.path.join(PROJECT_ROOT, "02_extract", "geo")


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


@pytest.fixture
def mock_env_gcs(monkeypatch):
    monkeypatch.setenv("STORAGE", "gcs")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
