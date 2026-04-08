import logging
import time
from datetime import datetime

import requests

import utils
from auth import create_authenticated_session, refresh_access_token
from config import Config, load_config

logger = logging.getLogger(__name__)

MAX_RESULTS = 3_150
PAGE_SIZE = 150
REQUEST_DELAY_SECONDS = 0.15
REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRY_ATTEMPTS = 3

REFERENTIAL_FILE_NAMES = {
    "metiers": "ref_metiers_rome.json",
    "domaines": "ref_domaines_rome.json",
    "secteursActivites": "ref_secteurs_activites.json",
    "typesContrats": "ref_types_contrats.json",
    "niveauxFormations": "ref_niveaux_formations.json",
    "permis": "ref_permis.json",
    "langues": "ref_langues.json",
}


def request_with_retry(
    session: requests.Session,
    config: Config,
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
) -> requests.Response:
    """
    Exécute une requête GET avec gestion homogène des erreurs réseau, des
    limitations de débit et des renouvellements de jeton.
    """

    for attempt_index in range(MAX_RETRY_ATTEMPTS):
        logger.info(
            "Sending France Travail request to %s (attempt %s/%s).",
            url,
            attempt_index + 1,
            MAX_RETRY_ATTEMPTS,
        )
        request_start_time = time.monotonic()
        try:
            response = session.get(
                url,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            logger.warning(
                "HTTP request failed for %s (attempt %s/%s): %s",
                url,
                attempt_index + 1,
                MAX_RETRY_ATTEMPTS,
                exc,
            )
            time.sleep(2**attempt_index)
            continue

        logger.info(
            "France Travail response received from %s with status %s in %.2f seconds.",
            url,
            response.status_code,
            time.monotonic() - request_start_time,
        )

        if response.status_code in (401, 403):
            logger.info("Access token expired or rejected. Refreshing session.")
            refresh_access_token(session, config)
            time.sleep(1)
            continue

        if response.status_code == 429:
            wait_seconds = 2 ** (attempt_index + 1)
            logger.warning(
                "Rate limit reached for %s. Waiting %s seconds before retry.",
                url,
                wait_seconds,
            )
            time.sleep(wait_seconds)
            continue

        if response.status_code == 204:
            return response

        response.raise_for_status()
        return response

    raise RuntimeError(
        f"Request failed after {MAX_RETRY_ATTEMPTS} attempts for URL: {url}"
    )


def build_search_label(search_parameters: dict) -> str:
    return search_parameters.get("codeROME") or search_parameters.get(
        "motsCles",
        "unknown_search",
    )


def parse_total_results_count(first_page_response: requests.Response) -> int:
    content_range_header = first_page_response.headers.get("Content-Range", "")

    try:
        return int(content_range_header.split("/")[1])
    except (IndexError, ValueError):
        results = first_page_response.json().get("resultats", [])
        return len(results)


class ReferentialsExtractor:
    """Extraction des référentiels France Travail."""

    def __init__(self, config: Config):
        self.config = config
        self.session = create_authenticated_session(config)
        logger.info("Referentials extractor initialized.")

    def extract(self) -> None:
        for (
            referential_endpoint,
            referential_file_name,
        ) in REFERENTIAL_FILE_NAMES.items():
            logger.info("Starting referential extraction: %s", referential_endpoint)
            referential_payload = self._fetch_referential(referential_endpoint)
            utils.save_json_payload(
                config=self.config,
                payload=referential_payload,
                destination_name=referential_file_name,
                gcs_prefix="raw_referentiels",
                local_directory=self.config.local_save_dir_refs,
            )
            logger.info("Completed referential extraction: %s", referential_endpoint)
            time.sleep(REQUEST_DELAY_SECONDS)

    def _fetch_referential(self, referential_endpoint: str) -> list[dict] | dict:
        referential_url = f"{self.config.referentiels_base_url}/{referential_endpoint}"
        response = request_with_retry(self.session, self.config, referential_url)
        return response.json()


class OffersExtractor:
    """Extraction des offres France Travail avec dédoublonnage par identifiant."""

    def __init__(self, config: Config, mode: str):
        self.config = config
        self.session = create_authenticated_session(config)
        self.offers_by_id: dict[str, dict] = {}
        self.total_offers_fetched = 0
        self.unique_offers_added_by_search_label: dict[str, int] = {}
        self.mode = mode
        logger.info(
            "Offers extractor initialized with mode=%s and %s search params.",
            mode,
            len(config.search_params or []),
        )

    def extract(self) -> None:
        if not self.config.search_params:
            raise ValueError("No search parameters were provided in the configuration.")

        for search_parameters in self.config.search_params:
            self._extract_search(search_parameters)

        self._save_results()

    def _extract_search(self, search_parameters: dict) -> None:
        search_label = build_search_label(search_parameters)
        logger.info("Starting offers extraction for search: %s", search_label)

        sorted_search_parameters = {**search_parameters, "sort": 2}
        first_page_response = request_with_retry(
            self.session,
            self.config,
            self.config.offres_base_url,
            params=sorted_search_parameters,
        )

        if first_page_response.status_code == 204:
            logger.info("No offer returned for search: %s", search_label)
            self.unique_offers_added_by_search_label[search_label] = 0
            return

        total_results_count = parse_total_results_count(first_page_response)
        if self.mode == "test":
            extraction_limit = min(total_results_count, 200)
        else:
            extraction_limit = min(total_results_count, MAX_RESULTS)
        added_unique_offers_for_search = 0

        logger.info(
            "Search %s returned %s offers. Extraction limit is %s.",
            search_label,
            total_results_count,
            extraction_limit,
        )

        for start_index in range(0, extraction_limit, PAGE_SIZE):
            end_index = min(start_index + PAGE_SIZE - 1, extraction_limit - 1)
            offers_page = self._fetch_page(
                sorted_search_parameters,
                start_index,
                end_index,
            )

            self.total_offers_fetched += len(offers_page)

            for offer_payload in offers_page:
                offer_id = offer_payload.get("id")
                if not offer_id or offer_id in self.offers_by_id:
                    continue

                self.offers_by_id[offer_id] = offer_payload
                added_unique_offers_for_search += 1

            logger.info(
                "Processed range %s-%s for search %s. %s offers fetched on page, %s unique offers accumulated.",
                start_index,
                end_index,
                search_label,
                len(offers_page),
                len(self.offers_by_id),
            )
            time.sleep(REQUEST_DELAY_SECONDS)

        self.unique_offers_added_by_search_label[search_label] = (
            added_unique_offers_for_search
        )
        logger.info(
            "Completed offers extraction for search %s. %s unique offers added.",
            search_label,
            added_unique_offers_for_search,
        )

    def _fetch_page(
        self,
        search_parameters: dict,
        start_index: int,
        end_index: int,
    ) -> list[dict]:
        page_parameters = {**search_parameters, "range": f"{start_index}-{end_index}"}
        page_headers = {"Range": f"offres {start_index}-{end_index}"}

        response = request_with_retry(
            self.session,
            self.config,
            self.config.offres_base_url,
            params=page_parameters,
            headers=page_headers,
        )
        return response.json().get("resultats", [])

    def _save_results(self) -> None:
        if not self.offers_by_id:
            logger.warning("No offer has been collected. Nothing will be saved.")
            return

        deduplicated_offers = list(self.offers_by_id.values())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_name = f"offres_data_market_{timestamp}.ndjson"

        utils.save_ndjson_records(
            config=self.config,
            records=deduplicated_offers,
            destination_name=output_file_name,
            gcs_prefix="raw_offres",
            local_directory=self.config.local_save_dir_offres,
        )

        logger.info(
            "Offers extraction completed. %s offers fetched, %s unique offers saved, %s duplicates removed.",
            self.total_offers_fetched,
            len(deduplicated_offers),
            self.total_offers_fetched - len(deduplicated_offers),
        )


def extract_referentials() -> None:
    logger.info("Preparing referentials extraction.")
    config = load_config()
    extractor = ReferentialsExtractor(config)
    extractor.extract()


def extract_offers(mode: str) -> None:
    logger.info("Preparing offers extraction with mode=%s.", mode)
    config = load_config()
    extractor = OffersExtractor(config, mode)
    extractor.extract()
