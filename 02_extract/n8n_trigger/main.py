import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
from shared import bigquery
from shared.storage import save_ndjson_records

logger = logging.getLogger(__name__)
_WEBHOOK_TIMEOUT_SECONDS = 120


def _env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


@dataclass
class _Config:
    storage: str | None
    gcs_bucket_name: str | None


def get_untracked_offers() -> list[dict]:
    query = f"""
        SELECT DISTINCT a.employer_name, a.nom_commune, e.siren
        FROM `{_env("INTERMEDIATE_DATASET_ID")}.int_adzuna_offres` a
        INNER JOIN `{_env("STAGING_DATASET_ID")}.staging_api_entreprise` e
            ON LOWER(TRIM(a.employer_name)) = LOWER(TRIM(e.employer_name))
            AND LOWER(TRIM(a.nom_commune)) = LOWER(TRIM(e.nom_commune))
        LEFT JOIN `{_env("STAGING_DATASET_ID")}.staging_societe_tracking` t
            ON LOWER(TRIM(a.employer_name)) = LOWER(TRIM(t.employer_name))
            AND LOWER(TRIM(a.nom_commune)) = LOWER(TRIM(t.nom_commune))
        WHERE t.employer_name IS NULL
          AND a.employer_name IS NOT NULL
          AND a.nom_commune IS NOT NULL
          AND e.siren IS NOT NULL
    """
    return bigquery.query_to_dicts(query)


def call_n8n_webhook(label: str, siren: str) -> dict:
    response = requests.get(
        _env("N8N_WEBHOOK_URL"),
        params={
            "denomination_unite_legales": label,
            "siren": siren,
        },
        timeout=_WEBHOOK_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected n8n response type: {type(payload).__name__}")
    return payload


def build_flat_record(scraped: dict, offer: dict, scraped_at: str) -> dict:
    adr = scraped.get("adresse", {}) or {}
    return {
        "employer_name": offer["employer_name"],
        "nom_commune": offer["nom_commune"],
        "siren": scraped.get("siren") or offer["siren"],
        "scraped_at": scraped_at,
        "siret_siege": scraped.get("siret_siege"),
        "tva_intra": scraped.get("tva_intra"),
        "legal_name": scraped.get("legal_name"),
        "naf_code": scraped.get("naf_code"),
        "naf_label": scraped.get("naf_label"),
        "date_creation": scraped.get("date_creation"),
        "adresse_rue": adr.get("rue"),
        "adresse_complement": adr.get("complement"),
        "adresse_code_postal": adr.get("code_postal"),
        "adresse_ville": adr.get("ville"),
        "forme_juridique_code": scraped.get("forme_juridique_code"),
        "statut": scraped.get("statut"),
        "dirigeants": scraped.get("dirigeants") or [],
        "capital_social": scraped.get("capital_social"),
        "convention_collective": scraped.get("convention_collective"),
        "noms_commerciaux": scraped.get("noms_commerciaux"),
        "statut_rcs": scraped.get("statut_rcs"),
        "statut_insee": scraped.get("statut_insee"),
        "statut_rne": scraped.get("statut_rne"),
        "chiffre_affaires": scraped.get("chiffre_affaires"),
        "effectif": scraped.get("effectif"),
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    to_process = get_untracked_offers()
    logger.info("Offers with SIREN to process: %d", len(to_process))
    if not to_process:
        logger.info("No matches found")
        return

    flat_records: list[dict] = []
    for item in to_process:
        try:
            scraped = call_n8n_webhook(item["employer_name"], item["siren"])
            flat_records.append(
                build_flat_record(
                    scraped,
                    item,
                    datetime.now(timezone.utc).isoformat(),
                )
            )
            logger.info("Scraped %s (%s)", item["employer_name"], item["siren"])
        except Exception:
            logger.exception("Failed for %s (%s)", item["employer_name"], item["siren"])

    if not flat_records:
        logger.warning("No results scraped")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    save_ndjson_records(
        config=_Config(storage="gcs", gcs_bucket_name=_env("GCS_BUCKET_NAME")),
        records=flat_records,
        destination_name=f"n8n_societe/{timestamp}.ndjson",
        gcs_prefix="raw",
        local_directory="02_extract/data",
    )

    tracking_rows = [
        {
            "employer_name": r["employer_name"],
            "nom_commune": r["nom_commune"],
            "processed_at": r["scraped_at"],
        }
        for r in flat_records
    ]
    bigquery.insert_rows(
        _env("STAGING_DATASET_ID"),
        "staging_societe_tracking",
        tracking_rows,
    )

    logger.info("Done - %d/%d processed", len(flat_records), len(to_process))


if __name__ == "__main__":
    main()
