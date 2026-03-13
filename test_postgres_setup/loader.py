"""
Loader script to insert France Travail JSON offers into PostgreSQL.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

import psycopg2
from psycopg2.extras import execute_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("db_loader")


@dataclass
class DBConfig:
    """Database configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = "francetravail_test"
    user: str = "test_user"
    password: str = "test_password"


class OffresLoader:
    """Load France Travail offers into PostgreSQL."""

    def __init__(self, config: DBConfig):
        self.config = config
        self.conn = None

    def connect(self) -> None:
        """Establish database connection."""
        self.conn = psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
        )
        logger.info("Connected to database '%s'", self.config.database)

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def load_offres(self, json_path: str) -> int:
        """Load offers from JSON file into database."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        resultats = data.get("resultats", [])
        logger.info("Loading %d offers from %s", len(resultats), json_path)

        offres_to_insert = []
        competences_to_insert = []
        permis_to_insert = []

        for offre in resultats:
            # Main offer data
            lieu = offre.get("lieuTravail", {})
            entreprise = offre.get("entreprise", {})

            offre_data = (
                offre.get("id"),
                offre.get("intitule"),
                offre.get("description"),
                offre.get("dateCreation"),
                offre.get("dateActualisation"),
                lieu.get("libelle"),
                lieu.get("latitude"),
                lieu.get("longitude"),
                lieu.get("codePostal"),
                lieu.get("commune"),
                offre.get("romeCode"),
                offre.get("romeLibelle"),
                offre.get("appellationlibelle"),
                entreprise.get("entrepriseAdaptee", False),
                offre.get("typeContrat"),
                offre.get("typeContratLibelle"),
                offre.get("natureContrat"),
                offre.get("experienceExige"),
                offre.get("experienceLibelle"),
                json.dumps(offre, ensure_ascii=False),  # raw_json
            )
            offres_to_insert.append(offre_data)

            # Competences
            for comp in offre.get("competences", []):
                competences_to_insert.append(
                    (offre.get("id"), comp.get("code"), comp.get("libelle"))
                )

            # Permis
            for perm in offre.get("permis", []):
                permis_to_insert.append(
                    (offre.get("id"), perm.get("libelle"), perm.get("exigence"))
                )

        with self.conn.cursor() as cur:
            # Insert offers
            if offres_to_insert:
                execute_batch(
                    cur,
                    """
                    INSERT INTO offres (
                        id, intitule, description, date_creation, date_actualisation,
                        lieu_travail_libelle, lieu_travail_latitude, lieu_travail_longitude,
                        lieu_travail_code_postal, lieu_travail_commune,
                        rome_code, rome_libelle, appellation_libelle,
                        entreprise_adaptee, type_contrat, type_contrat_libelle,
                        nature_contrat, experience_exige, experience_libelle, raw_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        intitule = EXCLUDED.intitule,
                        description = EXCLUDED.description,
                        date_actualisation = EXCLUDED.date_actualisation,
                        raw_json = EXCLUDED.raw_json,
                        updated_at = NOW()
                    """,
                    offres_to_insert,
                )
                logger.info("Inserted %d offers", len(offres_to_insert))

            # Insert competences
            if competences_to_insert:
                execute_batch(
                    cur,
                    """
                    INSERT INTO offres_competences (offre_id, competence_code, competence_libelle)
                    VALUES (%s, %s, %s)
                    """,
                    competences_to_insert,
                )
                logger.info("Inserted %d competences", len(competences_to_insert))

            # Insert permis
            if permis_to_insert:
                execute_batch(
                    cur,
                    """
                    INSERT INTO offres_permis (offre_id, permis_libelle, permis_exigence)
                    VALUES (%s, %s, %s)
                    """,
                    permis_to_insert,
                )
                logger.info("Inserted %d permis", len(permis_to_insert))

        self.conn.commit()
        return len(offres_to_insert)

    def get_offres_count(self) -> int:
        """Get total number of offers in database."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM offres")
            return cur.fetchone()[0]

    def get_offre_by_id(self, offre_id: str) -> dict | None:
        """Get a specific offer by ID."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, intitule, rome_code, type_contrat, raw_json FROM offres WHERE id = %s",
                (offre_id,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "intitule": row[1],
                    "rome_code": row[2],
                    "type_contrat": row[3],
                    "raw_json": row[4],
                }
            return None

    def clear_tables(self) -> None:
        """Clear all data from tables (for testing)."""
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE offres_permis, offres_competences, offres CASCADE")
        self.conn.commit()
        logger.info("All tables cleared")


def main():
    """Main entry point."""
    import os
    from pathlib import Path

    # Load config from environment or use defaults
    config = DBConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "francetravail_test"),
        user=os.getenv("DB_USER", "test_user"),
        password=os.getenv("DB_PASSWORD", "test_password"),
    )

    loader = OffresLoader(config)

    try:
        loader.connect()
        
        # Load test data
        fixture_path = Path(__file__).parent / "fixtures" / "test_offres.json"
        count = loader.load_offres(str(fixture_path))
        logger.info("Successfully loaded %d offers", count)
        
        # Verify
        total = loader.get_offres_count()
        logger.info("Total offers in database: %d", total)
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()
