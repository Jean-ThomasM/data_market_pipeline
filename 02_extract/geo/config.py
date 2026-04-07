import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    project_id: str | None
    gcs_bucket_name: str | None
    geo_api_base_url: str | None
    local_save_directory: str | None

    def validate(self) -> None:
        environment = os.getenv("ENV")
        if environment not in {"prod", "local"}:
            raise ValueError("Variable ENV doit être 'prod' ou 'local'")

        if environment == "prod" and not self.project_id:
            raise ValueError("GCP_PROJECT_ID non définie")

        if environment == "prod" and not self.gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME non définie")

        if not self.geo_api_base_url:
            raise ValueError("GEO_API_URL non définie")

        if environment == "local" and not self.local_save_directory:
            raise ValueError("Le répertoire local de sauvegarde GEO est non défini")


def load_config() -> Config:
    load_dotenv()

    config = Config(
        project_id=os.getenv("GCP_PROJECT_ID"),
        gcs_bucket_name=os.getenv("GCS_BUCKET_NAME", ""),
        geo_api_base_url=os.getenv("GEO_API_URL"),
        local_save_directory=str(
            Path(__file__).resolve().parent.parent / "data" / "geo"
        ),
    )
    config.validate()
    return config
