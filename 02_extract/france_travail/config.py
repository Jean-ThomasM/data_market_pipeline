import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from shared import gcs
from shared.secrets import get_secrets

logger = logging.getLogger(__name__)


def build_default_search_params() -> list[dict[str, str]]:
    return [
        {"codeROME": os.getenv("FT_ROME_CODE", "M1811")},
        {"motsCles": "data engineer"},
        {"motsCles": "architecte data"},
        {"motsCles": "data ingénieur"},
        {"motsCles": "ingénieur data"},
        {"motsCles": "data architect"},
    ]


@dataclass
class Config:
    project_id: str | None
    storage: str | None
    ft_client_id: str | None
    ft_client_key: str | None
    scope: str | None
    gcs_bucket_name: str | None
    token_url: str | None
    offres_base_url: str | None
    referentiels_base_url: str | None
    local_save_dir_offres: str | None
    local_save_dir_refs: str | None
    search_params: list | None

    def validate(self) -> None:
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID non définie")
        if not self.ft_client_id:
            raise ValueError("FT_CLIENT_ID non définie")
        if not self.ft_client_key:
            raise ValueError("FT_CLIENT_KEY non définie")


def load_config() -> Config:
    load_dotenv()
    project_id = os.getenv("GCP_PROJECT_ID")
    gcs_bucket_name: str = os.getenv("GCS_BUCKET_NAME", "")
    storage = os.getenv("STORAGE")
    logger.info("Loading France Travail config with storage=%s.", storage)
    if storage == "gcs":
        logger.info("Fetching France Travail credentials from Secret Manager.")
        ft_client_id = get_secrets(project_id, "FT_CLIENT_ID")
        ft_client_key = get_secrets(project_id, "FT_CLIENT_KEY")
        local_save_dir_offres = None
        local_save_dir_refs = None
        search_params_object = os.getenv(
            "FT_SEARCH_PARAMS_OBJECT",
            f"config/search_params_{storage}.json",
        )
        logger.info(
            "Loading France Travail search params from GCS object: %s/%s.",
            gcs_bucket_name,
            search_params_object,
        )
        try:
            search_params = json.loads(
                gcs.read_file(gcs_bucket_name, search_params_object)
            )
        except NotFound:
            logger.warning(
                "Search params object not found in GCS: %s/%s. Falling back to default search parameters.",
                gcs_bucket_name,
                search_params_object,
            )
            search_params = build_default_search_params()
        logger.info(
            "France Travail search params ready: %s entries loaded.",
            len(search_params),
        )
    elif storage == "local":
        ft_client_id = os.getenv("FT_CLIENT_ID")
        ft_client_key = os.getenv("FT_CLIENT_KEY")
        local_save_dir_offres: str = str(
            Path(__file__).resolve().parent.parent / "data" / "france_travail_offres"
        )
        local_save_dir_refs: str = str(
            Path(__file__).resolve().parent.parent
            / "data"
            / "france_travail_referentiels"
        )
        search_params = build_default_search_params()
        logger.info(
            "Using local France Travail config with %s default search params.",
            len(search_params),
        )
    else:
        raise ValueError("Variable STORAGE doit être 'gcs' ou 'local'")

    scope: str = os.getenv("SCOPE_API_FT_EMPLOI", "api_offresdemploiv2 o2dsoffre")

    token_url: str = (
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
        "?realm=%2Fpartenaire"
    )
    offres_base_url: str = (
        "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    )
    referentiels_base_url: str = (
        "https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel"
    )
    config = Config(
        project_id=project_id,
        ft_client_id=ft_client_id,
        ft_client_key=ft_client_key,
        local_save_dir_refs=local_save_dir_refs,
        local_save_dir_offres=local_save_dir_offres,
        scope=scope,
        gcs_bucket_name=gcs_bucket_name,
        token_url=token_url,
        offres_base_url=offres_base_url,
        referentiels_base_url=referentiels_base_url,
        search_params=search_params,
        storage=storage,
    )
    config.validate()
    logger.info("France Travail config validation completed.")
    return config
