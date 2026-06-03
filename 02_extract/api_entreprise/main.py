import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import api as api_entreprise
from shared.storage import save_ndjson_records

logger = logging.getLogger(__name__)


def _env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


@dataclass
class _Config:
    storage: str | None
    gcs_bucket_name: str | None


def get_all_offers() -> list[dict]:
    query = f"""
        SELECT DISTINCT a.employer_name, a.nom_commune
        FROM `{_env("INTERMEDIATE_DATASET_ID")}.int_adzuna_offres` a
        WHERE a.employer_name IS NOT NULL
          AND a.nom_commune IS NOT NULL
          AND LOWER(TRIM(a.employer_name)) NOT LIKE '%anonyme%'
    """
    from shared import bigquery as bq_shared

    return bq_shared.query_to_dicts(query)


def build_flat_record(offer: dict, api_data: dict, enriched_at: str) -> dict:
    adr = api_data.get("adresse", {}) or {}
    base = {
        k: v
        for k, v in api_data.items()
        if k not in ("adresse", "dirigeants", "finances", "liste_idcc")
    }
    return {
        **base,
        "employer_name": offer["employer_name"],
        "nom_commune": offer["nom_commune"],
        "siren": api_data.get("siren"),
        "enriched_at": enriched_at,
        "adresse_numero_voie": adr.get("numero_voie"),
        "adresse_type_voie": adr.get("type_voie"),
        "adresse_libelle_voie": adr.get("libelle_voie"),
        "adresse_complement": adr.get("complement_adresse"),
        "adresse_code_postal": adr.get("code_postal"),
        "adresse_libelle_commune": adr.get("libelle_commune"),
        "adresse_code_commune": adr.get("code_commune"),
        "liste_idcc": api_data.get("liste_idcc") or [],
        "dirigeants": api_data.get("dirigeants") or [],
        "finances": [
            {
                "annee": year,
                "ca": info.get("ca"),
                "resultat_net": info.get("resultat_net"),
            }
            for year, info in (api_data.get("finances") or {}).items()
        ],
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    offers = get_all_offers()
    logger.info("Offers to process: %d", len(offers))
    if not offers:
        logger.info("No offers to process")
        return

    flat_records: list[dict] = []
    for item in offers:
        data = api_entreprise.search_by_name_city(
            item["employer_name"],
            item.get("nom_commune"),
        )
        if data is not None:
            flat_records.append(
                build_flat_record(
                    item,
                    data,
                    datetime.now(timezone.utc).isoformat(),
                )
            )
            if item.get("nom_commune"):
                logger.info(
                    "Enriched %s / %s (siren=%s)",
                    item["employer_name"],
                    item["nom_commune"],
                    data.get("siren"),
                )
            else:
                logger.info(
                    "Enriched %s (siren=%s)",
                    item["employer_name"],
                    data.get("siren"),
                )
        else:
            loc = f" / {item['nom_commune']}" if item.get("nom_commune") else ""
            logger.warning("No data for %s%s", item["employer_name"], loc)

    if not flat_records:
        logger.warning("No results enriched")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    save_ndjson_records(
        config=_Config(storage="gcs", gcs_bucket_name=_env("GCS_BUCKET_NAME")),
        records=flat_records,
        destination_name=f"api_entreprise/{timestamp}.ndjson",
        gcs_prefix="raw",
        local_directory="02_extract/data",
    )

    logger.info("Done — %d/%d enriched", len(flat_records), len(offers))


if __name__ == "__main__":
    main()
