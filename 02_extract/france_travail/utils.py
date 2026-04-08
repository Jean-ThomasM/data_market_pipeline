import json
import logging
from pathlib import Path

from shared import gcs

from config import Config

logger = logging.getLogger(__name__)


def save_text_content(
    config: Config,
    content: str,
    destination_name: str,
    gcs_prefix: str,
    local_directory: str | None,
) -> None:
    """
    Persiste un contenu texte dans GCS, ou dans un répertoire local lorsque
    le backend de stockage configuré est local.
    """

    if config.storage == "gcs":
        if not config.gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME est requis lorsque STORAGE=gcs.")

        gcs_path = f"{gcs_prefix}/{destination_name}"
        gcs.write_file(config.gcs_bucket_name, gcs_path, content.encode("utf-8"))
        logger.info("Saved file to GCS: %s", gcs_path)
        return

    if not local_directory:
        raise ValueError("A local output directory is required when STORAGE=local.")

    output_directory = Path(local_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / destination_name
    output_path.write_text(content, encoding="utf-8")
    logger.info("Saved file locally: %s", output_path)


def save_json_payload(
    config: Config,
    payload: list[dict] | dict,
    destination_name: str,
    gcs_prefix: str,
    local_directory: str | None,
) -> None:
    json_content = json.dumps(payload, ensure_ascii=False, indent=2)
    save_text_content(
        config=config,
        content=json_content,
        destination_name=destination_name,
        gcs_prefix=gcs_prefix,
        local_directory=local_directory,
    )


def save_ndjson_records(
    config: Config,
    records: list[dict],
    destination_name: str,
    gcs_prefix: str,
    local_directory: str | None,
) -> None:
    ndjson_content = "\n".join(
        json.dumps(record, ensure_ascii=False) for record in records
    )
    save_text_content(
        config=config,
        content=ndjson_content,
        destination_name=destination_name,
        gcs_prefix=gcs_prefix,
        local_directory=local_directory,
    )
