"""Configuration pytest pour les tests d'intégration."""

import os
import sys
from pathlib import Path

import pytest

# ── Module-level isolation ──────────────────────────────────────────────
# Clear cached extractor modules BEFORE any test module in this dir is
# imported.  Each test file does sys.path.insert(0, …) at module level,
# so the freshly imported modules will come from the correct extractor.
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

for _k in list(sys.modules):
    _m = sys.modules[_k]
    _f = getattr(_m, "__file__", None)
    if _f and "02_extract" in os.path.normpath(_f):
        sys.modules.pop(_k, None)

for _p in list(sys.path):
    _norm = os.path.normpath(_p) if _p else ""
    if "02_extract" in _norm:
        sys.path.remove(_p)


_EXTRACTOR_MAP = {
    "france_travail": "france_travail",
    "geo": "geo",
    "health": None,
}


@pytest.fixture(autouse=True)
def _isolate_extractor_imports(request):
    module_name = Path(request.module.__file__).stem
    extractor = None
    for key, val in _EXTRACTOR_MAP.items():
        if key in module_name:
            extractor = val
            break

    if extractor is None:
        yield
        return

    my_src = str(Path(_PROJECT_ROOT) / "02_extract" / extractor)

    old_path = list(sys.path)
    old_modules = {}
    for k, v in list(sys.modules.items()):
        f = getattr(v, "__file__", None)
        if f and "02_extract" in os.path.normpath(f):
            old_modules[k] = sys.modules.pop(k)
    for p in list(sys.path):
        normalized = os.path.normpath(p) if p else _PROJECT_ROOT
        if normalized == _PROJECT_ROOT or (
            "02_extract" in normalized and normalized != my_src
        ):
            sys.path.remove(p)
    if my_src not in sys.path:
        sys.path.insert(0, my_src)
    yield
    sys.path[:] = old_path
    sys.modules.update(old_modules)


@pytest.fixture
def mock_local_storage(tmp_path):
    """Crée un répertoire de stockage local temporaire par test."""
    storage_dir = tmp_path / "mock_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return str(storage_dir)


@pytest.fixture
def env_vars_local(mock_local_storage):
    """Configure les variables d'environnement pour le mode local."""
    original_env = dict(os.environ)

    os.environ["STORAGE"] = "local"
    os.environ["GCP_PROJECT_ID"] = "test-project"
    os.environ["GCS_BUCKET_NAME"] = "test-bucket"

    yield

    # Restaure les variables d'environnement
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_ft_offers():
    """Fournit des exemples d'offres France Travail pour les tests."""
    return [
        {
            "id": "123456789",
            "intitule": "Data Engineer",
            "description": "Recherche Data Engineer expérimenté",
            "dateCreation": "2024-01-15T10:00:00.000Z",
            "lieuTravail": {
                "libelle": "Paris",
                "codePostal": "75001",
            },
            "romeCode": "M1811",
            "typeContrat": "CDI",
        },
        {
            "id": "987654321",
            "intitule": "Data Architect",
            "description": "Architecte data senior",
            "dateCreation": "2024-01-14T08:00:00.000Z",
            "lieuTravail": {
                "libelle": "Lyon",
                "codePostal": "69001",
            },
            "romeCode": "M1811",
            "typeContrat": "CDI",
        },
    ]


@pytest.fixture
def sample_geo_communes():
    """Fournit des exemples de communes pour les tests."""
    return [
        {
            "nom": "Paris",
            "code": "75056",
            "codeDepartement": "75",
            "codeRegion": "11",
            "codesPostaux": ["75001", "75002", "75003"],
            "population": 2161000,
        },
        {
            "nom": "Lyon",
            "code": "69123",
            "codeDepartement": "69",
            "codeRegion": "84",
            "codesPostaux": ["69001", "69002", "69003"],
            "population": 515000,
        },
    ]
