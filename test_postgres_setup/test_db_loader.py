"""
Pytest tests for France Travail PostgreSQL loader.
"""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
import psycopg2

from loader import DBConfig, OffresLoader


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def db_config():
    """Database configuration fixture."""
    return DBConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "francetravail_test"),
        user=os.getenv("DB_USER", "test_user"),
        password=os.getenv("DB_PASSWORD", "test_password"),
    )


@pytest.fixture(scope="module")
def postgres_container():
    """Start PostgreSQL container before tests and stop after."""
    compose_file = Path(__file__).parent / "docker-compose.yml"
    
    # Stop any existing container
    subprocess.run(
        ["docker-compose", "down", "-v"],
        cwd=Path(__file__).parent,
        capture_output=True,
    )
    
    # Start container
    subprocess.run(
        ["docker-compose", "up", "-d"],
        cwd=Path(__file__).parent,
        check=True,
        capture_output=True,
    )
    
    # Wait for PostgreSQL to be ready
    max_wait = 30
    waited = 0
    while waited < max_wait:
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="francetravail_test",
                user="test_user",
                password="test_password",
            )
            conn.close()
            break
        except psycopg2.OperationalError:
            time.sleep(1)
            waited += 1
    else:
        raise RuntimeError("PostgreSQL container did not become ready in time")
    
    yield
    
    # Cleanup
    subprocess.run(
        ["docker-compose", "down", "-v"],
        cwd=Path(__file__).parent,
        capture_output=True,
    )


@pytest.fixture
def loader(db_config, postgres_container):
    """Loader fixture with clean database."""
    l = OffresLoader(db_config)
    l.connect()
    l.clear_tables()
    yield l
    l.close()


@pytest.fixture
def test_data_path():
    """Path to test fixture."""
    return Path(__file__).parent / "fixtures" / "test_offres.json"


# =============================================================================
# Tests
# =============================================================================

class TestOffresLoader:
    """Tests for OffresLoader class."""

    def test_load_offres_count(self, loader, test_data_path):
        """Test that loading inserts correct number of offers."""
        count = loader.load_offres(str(test_data_path))
        assert count == 5
        
        db_count = loader.get_offres_count()
        assert db_count == 5

    def test_load_offres_data(self, loader, test_data_path):
        """Test that offer data is correctly inserted."""
        loader.load_offres(str(test_data_path))
        
        offre = loader.get_offre_by_id("TEST001")
        assert offre is not None
        assert offre["intitule"] == "Data Engineer (H/F)"
        assert offre["rome_code"] == "M1811"
        assert offre["type_contrat"] == "CDI"

    def test_load_offres_raw_json(self, loader, test_data_path):
        """Test that raw JSON is stored correctly."""
        loader.load_offres(str(test_data_path))
        
        offre = loader.get_offre_by_id("TEST001")
        raw_json = json.loads(offre["raw_json"])
        assert raw_json["id"] == "TEST001"
        assert raw_json["lieuTravail"]["codePostal"] == "75001"

    def test_load_competences(self, loader, test_data_path, db_config):
        """Test that competences are inserted."""
        loader.load_offres(str(test_data_path))
        
        with psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM offres_competences")
                count = cur.fetchone()[0]
                assert count == 10  # 2 competences per offer * 5 offers

    def test_load_permis(self, loader, test_data_path, db_config):
        """Test that permis are inserted."""
        loader.load_offres(str(test_data_path))
        
        with psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM offres_permis")
                count = cur.fetchone()[0]
                assert count == 2  # Only 2 offers have permis

    def test_upsert_on_conflict(self, loader, test_data_path):
        """Test that loading same data twice doesn't duplicate."""
        loader.load_offres(str(test_data_path))
        loader.load_offres(str(test_data_path))
        
        db_count = loader.get_offres_count()
        assert db_count == 5  # Should still be 5, not 10

    def test_clear_tables(self, loader, test_data_path):
        """Test that clear_tables removes all data."""
        loader.load_offres(str(test_data_path))
        loader.clear_tables()
        
        db_count = loader.get_offres_count()
        assert db_count == 0

    def test_query_by_rome_code(self, loader, test_data_path, db_config):
        """Test querying offers by ROME code."""
        loader.load_offres(str(test_data_path))
        
        with psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM offres WHERE rome_code = %s",
                    ("M1811",),
                )
                count = cur.fetchone()[0]
                assert count == 5

    def test_query_by_contrat_type(self, loader, test_data_path, db_config):
        """Test querying offers by contract type."""
        loader.load_offres(str(test_data_path))
        
        with psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM offres WHERE type_contrat = %s",
                    ("CDI",),
                )
                count = cur.fetchone()[0]
                assert count == 4  # 4 CDI, 1 CDD

    def test_jsonb_queries(self, loader, test_data_path, db_config):
        """Test JSONB field queries."""
        loader.load_offres(str(test_data_path))
        
        with psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.user,
            password=db_config.password,
        ) as conn:
            with conn.cursor() as cur:
                # Query using JSONB operator
                cur.execute(
                    """
                    SELECT COUNT(*) FROM offres 
                    WHERE raw_json->>'entrepriseAdaptee' = 'true'
                    """
                )
                count = cur.fetchone()[0]
                assert count == 1  # Only TEST003 has entrepriseAdaptee=true
