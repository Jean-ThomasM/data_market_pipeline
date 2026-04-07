import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from shared import gcs
from shared.secrets import get_secrets


@dataclass
class Config:
    project_id: str | None
    env: str | None
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
    env = os.getenv("ENV")
    if env == "prod":
        ft_client_id = get_secrets(project_id, "FT_CLIENT_ID")
        ft_client_key = get_secrets(project_id, "FT_CLIENT_KEY")
        local_save_dir_offres = None
        local_save_dir_refs = None
        search_params_object = os.getenv(
            "FT_SEARCH_PARAMS_OBJECT",
            f"config/search_params_{os.getenv('ENV', 'prod')}.json",
        )
        search_params = json.loads(gcs.read_file(gcs_bucket_name, search_params_object))
    elif env == "local":
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
        search_params: list = [
            {"codeROME": os.getenv("FT_ROME_CODE", "M1811")},
            {"motsCles": "data engineer"},
            {"motsCles": "architecte data"},
            {"motsCles": "data ingénieur"},
            {"motsCles": "ingénieur data"},
            {"motsCles": "data architect"},
        ]
    else:
        raise ValueError("Variable ENV doit être 'prod' ou 'local'")

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
        env=env,
    )
    config.validate()
    return config
