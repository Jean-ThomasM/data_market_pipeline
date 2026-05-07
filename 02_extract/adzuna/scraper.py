import logging
import os
import time
from datetime import datetime

import requests
import utils
from config import Config, load_config
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def request_with_retry(
    session: requests.Session,
    config: Config,
    page_url: str,
    *,
    params: dict | None = None,
) -> requests.Response:
    for attempt_index in range(MAX_RETRY_ATTEMPTS):
        logger.info(
            "Sending Adzuna request to %s (attempt %s/%s).",
            page_url,
            attempt_index + 1,
            MAX_RETRY_ATTEMPTS,
        )
        request_start_time = time.monotonic()
        try:
            response = session.get(
                page_url,
                params=params,
                timeout=config.request_timeout_seconds,
            )
        except requests.RequestException as exc:
            logger.warning(
                "HTTP request failed for %s (attempt %s/%s): %s",
                page_url,
                attempt_index + 1,
                MAX_RETRY_ATTEMPTS,
                exc,
            )
            time.sleep(2**attempt_index)
            continue

        logger.info(
            "Adzuna response received from %s with status %s in %.2f seconds.",
            page_url,
            response.status_code,
            time.monotonic() - request_start_time,
        )

        if response.status_code in RETRYABLE_STATUS_CODES:
            wait_seconds = 2 ** (attempt_index + 1)
            logger.warning(
                "Retryable Adzuna status %s for %s. Waiting %s seconds before retry.",
                response.status_code,
                page_url,
                wait_seconds,
            )
            time.sleep(wait_seconds)
            continue

        response.raise_for_status()
        return response

    raise RuntimeError(
        f"Request failed after {MAX_RETRY_ATTEMPTS} attempts for URL: {page_url}"
    )


def build_search_label(search_parameters: dict) -> str:
    return search_parameters.get("what") or search_parameters.get(
        "title_only",
        "unknown_search",
    )


class OffersExtractor:
    """Extraction des offres Adzuna avec pagination et dédoublonnage par identifiant."""

    def __init__(self, config: Config, mode: str):
        self.config = config
        self.session = requests.Session()
        self.offers_by_id: dict[str, dict] = {}
        self.total_offers_fetched = 0
        self.unique_offers_added_by_search_label: dict[str, int] = {}
        self.mode = mode
        logger.info(
            "Adzuna offers extractor initialized with mode=%s and %s search params.",
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
        logger.info("Starting Adzuna offers extraction for search: %s", search_label)

        first_page_payload = self._fetch_page(search_parameters, page=1)
        total_results_count = int(first_page_payload.get("count", 0) or 0)
        extraction_limit = self._build_extraction_limit(total_results_count)
        added_unique_offers_for_search = 0

        logger.info(
            "Adzuna search %s returned %s offers. Extraction limit is %s.",
            search_label,
            total_results_count,
            extraction_limit,
        )

        if extraction_limit == 0:
            self.unique_offers_added_by_search_label[search_label] = 0
            return

        page = 1
        while (page - 1) * self.config.results_per_page < extraction_limit:
            if page == 1:
                page_payload = first_page_payload
            else:
                page_payload = self._fetch_page(search_parameters, page=page)

            offers_page = page_payload.get("results", [])
            if not offers_page:
                break

            self.total_offers_fetched += len(offers_page)
            for offer_payload in offers_page:
                offer_id = str(offer_payload.get("id") or "")
                if not offer_id or offer_id in self.offers_by_id:
                    continue

                self.offers_by_id[offer_id] = offer_payload
                added_unique_offers_for_search += 1

            logger.info(
                "Processed Adzuna page %s for search %s. %s offers fetched on page, %s unique offers accumulated.",
                page,
                search_label,
                len(offers_page),
                len(self.offers_by_id),
            )

            if len(offers_page) < self.config.results_per_page:
                break

            page += 1
            time.sleep(self.config.request_delay_seconds)

        self.unique_offers_added_by_search_label[search_label] = (
            added_unique_offers_for_search
        )
        logger.info(
            "Completed Adzuna offers extraction for search %s. %s unique offers added.",
            search_label,
            added_unique_offers_for_search,
        )

    def _build_extraction_limit(self, total_results_count: int) -> int:
        if self.mode == "test":
            return min(total_results_count, 200)

        return min(total_results_count, self.config.max_results)

    def _fetch_page(self, search_parameters: dict, page: int) -> dict:
        page_url = f"{self.config.jobs_base_url}/{self.config.country}/search/{page}"
        page_parameters = {
            "app_id": self.config.adzuna_app_id,
            "app_key": self.config.adzuna_app_key,
            "results_per_page": self.config.results_per_page,
            "content-type": "application/json",
            **search_parameters,
        }
        if self.config.sort_by:
            page_parameters["sort_by"] = self.config.sort_by

        response = request_with_retry(
            self.session,
            self.config,
            page_url,
            params=page_parameters,
        )
        return response.json()

    def _save_results(self) -> None:
        if not self.offers_by_id:
            logger.warning("No Adzuna offer has been collected. Nothing will be saved.")
            return

        deduplicated_offers = list(self.offers_by_id.values())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_name = f"offres_adzuna_data_market_{timestamp}.ndjson"

        utils.save_ndjson_records(
            config=self.config,
            records=deduplicated_offers,
            destination_name=output_file_name,
            gcs_prefix="raw_offres_adzuna",
            local_directory=self.config.local_save_dir_offres,
        )

        logger.info(
            """Adzuna offers extraction completed. %s offers fetched,
            %s unique offers saved, %s duplicates removed.""",
            self.total_offers_fetched,
            len(deduplicated_offers),
            self.total_offers_fetched - len(deduplicated_offers),
        )


def extract_offers(mode: str) -> None:
    logger.info("Preparing Adzuna offers extraction with mode=%s.", mode)
    config = load_config()
    extractor = OffersExtractor(config, mode)
    extractor.extract()


def main() -> None:
    load_dotenv()
    mode = os.getenv("ADZUNA_EXTRACT_MODE", "prod").strip().lower()
    if mode not in {"prod", "test"}:
        raise ValueError("ADZUNA_EXTRACT_MODE doit valoir 'prod' ou 'test'.")

    logger.info("Starting Adzuna batch extraction with mode: %s", mode)
    extract_offers(mode=mode)
    logger.info("Adzuna batch extraction completed with mode: %s", mode)


if __name__ == "__main__":
    main()
