import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from shared import gcs
from shared.secrets import get_secrets

logger = logging.getLogger(__name__)


def build_default_search_params() -> list[dict[str, str]]:
    return [
        {"what": "data+engineer"},
    ]


def _normalize_search_params(raw_search_params: Any) -> list[dict[str, str]]:
    if not raw_search_params:
        return build_default_search_params()

    normalized_search_params: list[dict[str, str]] = []
    for search_param in raw_search_params:
        if isinstance(search_param, str):
            normalized_search_params.append({"what": search_param})
            continue

        if isinstance(search_param, dict):
            normalized_search_params.append(
                {str(key): str(value) for key, value in search_param.items()}
            )
            continue

        raise ValueError(
            "Les paramètres de recherche Adzuna doivent être des chaînes ou des objets."
        )

    return normalized_search_params


def _load_local_search_params() -> list[dict[str, str]]:
    raw_search_params = os.getenv("ADZUNA_SEARCH_PARAMS_JSON")
    if not raw_search_params:
        return build_default_search_params()

    return _normalize_search_params(json.loads(raw_search_params))


@dataclass
class Config:
    project_id: str | None
    storage: str | None
    adzuna_app_id: str | None
    adzuna_app_key: str | None
    gcs_bucket_name: str | None
    jobs_base_url: str
    country: str
    local_save_dir_offres: str | None
    search_params: list[dict[str, str]]
    results_per_page: int
    max_results: int
    request_delay_seconds: float
    request_timeout_seconds: float
    sort_by: str | None

    def validate(self) -> None:
        if self.storage not in {"gcs", "local"}:
            raise ValueError("Variable STORAGE doit être 'gcs' ou 'local'")
        if self.storage == "gcs" and not self.project_id:
            raise ValueError("GCP_PROJECT_ID non définie")
        if self.storage == "gcs" and not self.gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME non définie")
        if not self.adzuna_app_id:
            raise ValueError("ADZUNA_API_ID ou ADZUNA_APP_ID non définie")
        if not self.adzuna_app_key:
            raise ValueError("ADZUNA_API_KEY ou ADZUNA_APP_KEY non définie")
        if not self.search_params:
            raise ValueError("Aucun paramètre de recherche Adzuna fourni")
        if not 1 <= self.results_per_page <= 50:
            raise ValueError("ADZUNA_RESULTS_PER_PAGE doit être compris entre 1 et 50")
        if self.max_results < 1:
            raise ValueError("ADZUNA_MAX_RESULTS doit être supérieur ou égal à 1")


def _get_local_adzuna_app_id() -> str | None:
    return os.getenv("ADZUNA_API_ID") or os.getenv("ADZUNA_APP_ID")


def _get_local_adzuna_app_key() -> str | None:
    return os.getenv("ADZUNA_API_KEY") or os.getenv("ADZUNA_APP_KEY")


def _load_gcs_search_params(gcs_bucket_name: str) -> list[dict[str, str]]:
    search_params_object = os.getenv(
        "ADZUNA_SEARCH_PARAMS_OBJECT",
        "config/search_params_adzuna_gcs.json",
    )
    logger.info(
        "Loading Adzuna search params from GCS object: %s/%s.",
        gcs_bucket_name,
        search_params_object,
    )
    try:
        raw_search_params = json.loads(
            gcs.read_file(gcs_bucket_name, search_params_object)
        )
    except NotFound:
        logger.warning(
            "Search params object not found in GCS: %s/%s. Falling back to default search parameters.",
            gcs_bucket_name,
            search_params_object,
        )
        return build_default_search_params()

    return _normalize_search_params(raw_search_params)


def load_config() -> Config:
    load_dotenv()

    storage = os.getenv("STORAGE")
    project_id = os.getenv("GCP_PROJECT_ID")
    gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "")

    logger.info("Loading Adzuna config with storage=%s.", storage)

    if storage == "gcs":
        if not project_id:
            raise ValueError("GCP_PROJECT_ID non définie")
        if not gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME non définie")

        logger.info("Fetching Adzuna credentials from Secret Manager.")
        adzuna_app_id = get_secrets(
            project_id,
            os.getenv("ADZUNA_APP_ID_SECRET_NAME", "ADZUNA_API_ID"),
        )
        adzuna_app_key = get_secrets(
            project_id,
            os.getenv("ADZUNA_APP_KEY_SECRET_NAME", "ADZUNA_API_KEY"),
        )
        local_save_dir_offres = None
        search_params = _load_gcs_search_params(gcs_bucket_name)
    elif storage == "local":
        adzuna_app_id = _get_local_adzuna_app_id()
        adzuna_app_key = _get_local_adzuna_app_key()
        local_save_dir_offres = str(
            Path(__file__).resolve().parent.parent / "data" / "adzuna"
        )
        search_params = _load_local_search_params()
    else:
        raise ValueError("Variable STORAGE doit être 'gcs' ou 'local'")

    config = Config(
        project_id=project_id,
        storage=storage,
        adzuna_app_id=adzuna_app_id,
        adzuna_app_key=adzuna_app_key,
        gcs_bucket_name=gcs_bucket_name,
        jobs_base_url=os.getenv(
            "ADZUNA_JOBS_BASE_URL",
            "https://api.adzuna.com/v1/api/jobs",
        ),
        country=os.getenv("ADZUNA_COUNTRY", "fr"),
        local_save_dir_offres=local_save_dir_offres,
        search_params=search_params,
        results_per_page=int(os.getenv("ADZUNA_RESULTS_PER_PAGE", "50")),
        max_results=int(os.getenv("ADZUNA_MAX_RESULTS", "3150")),
        request_delay_seconds=float(os.getenv("ADZUNA_REQUEST_DELAY_SECONDS", "1.0")),
        request_timeout_seconds=float(
            os.getenv("ADZUNA_REQUEST_TIMEOUT_SECONDS", "30")
        ),
        sort_by=os.getenv("ADZUNA_SORT_BY", "date") or None,
    )
    config.validate()
    logger.info("Adzuna config validation completed.")
    return config
