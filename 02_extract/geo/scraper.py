import json
import logging
from pathlib import Path

import requests
from config import Config, load_config
from shared import gcs

logger = logging.getLogger(__name__)

GEO_API_BASE_URL = "https://geo.api.gouv.fr"
REQUEST_TIMEOUT_SECONDS = 30

RESOURCE_PATHS = {
    "regions": "/regions",
    "departements": "/departements",
    "communes": "/communes",
    "epcis": "/epcis",
}

RESOURCE_FILE_NAMES = {
    "regions": "regions.json",
    "departements": "departements.json",
    "communes": "communes.json",
    "epcis": "epcis.json",
}


def use_gcs_storage(config: Config) -> bool:
    return config.storage == "gcs"


def save_json_payload(
    config: Config,
    payload: list[dict] | dict,
    destination_name: str,
) -> None:
    json_content = json.dumps(payload, ensure_ascii=False, indent=2)

    if use_gcs_storage(config):
        gcs_path = f"raw_geo/{destination_name}"
        gcs.write_file(config.gcs_bucket_name, gcs_path, json_content.encode("utf-8"))
        logger.info("Saved GEO file to GCS: %s", gcs_path)
        return

    output_directory = Path(config.local_save_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / destination_name
    output_path.write_text(json_content, encoding="utf-8")
    logger.info("Saved GEO file locally: %s", output_path)


class GeoExtractor:
    """Extraction des référentiels GEO depuis geo.api.gouv.fr."""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()

    def extract(self) -> None:
        for resource_name in RESOURCE_PATHS:
            resource_payload = self._fetch_resource(resource_name)
            save_json_payload(
                config=self.config,
                payload=resource_payload,
                destination_name=RESOURCE_FILE_NAMES[resource_name],
            )

    def _fetch_resource(self, resource_name: str) -> list[dict]:
        resource_path = RESOURCE_PATHS[resource_name]
        resource_url = f"{GEO_API_BASE_URL}{resource_path}"

        try:
            response = self.session.get(resource_url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Erreur API GEO pour {resource_url}: {exc}") from exc

        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError(
                f"Réponse inattendue pour la ressource GEO '{resource_name}'"
            )

        logger.info(
            "Fetched GEO resource %s with %s records.",
            resource_name,
            len(payload),
        )
        return payload


def extract_geo() -> None:
    config = load_config()
    extractor = GeoExtractor(config)
    extractor.extract()
