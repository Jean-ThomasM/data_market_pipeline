import logging
from typing import Any

from google.cloud import bigquery

logger = logging.getLogger(__name__)


def get_client() -> bigquery.Client:
    return bigquery.Client()


def query_to_dicts(query: str) -> list[dict[str, Any]]:
    rows = get_client().query(query).result()
    return [dict(row) for row in rows]


def insert_rows(
    dataset_id: str,
    table_id: str,
    rows: list[dict[str, Any]],
) -> None:
    errors = get_client().insert_rows_json(
        f"{get_client().project}.{dataset_id}.{table_id}", rows
    )
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")
