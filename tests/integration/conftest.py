"""Configuration pytest pour les tests d'intégration."""

import os
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def integration_test_dir():
    """Crée un répertoire temporaire pour les tests d'intégration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_gcs_bucket(integration_test_dir):
    """Simule un bucket GCS avec un répertoire local."""
    bucket_dir = integration_test_dir / "mock_gcs_bucket"
    bucket_dir.mkdir(parents=True, exist_ok=True)
    return str(bucket_dir)


@pytest.fixture
def mock_local_storage(integration_test_dir):
    """Crée un répertoire de stockage local pour les tests."""
    storage_dir = integration_test_dir / "mock_storage"
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
