from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT_DIR / "02_extract" / "data" / "france_travail_offres"
DEFAULT_SCHEMA_PATH = (
    ROOT_DIR
    / "00_infra"
    / "opentofu"
    / "environments"
    / "dev"
    / "schemas"
    / "staging_offres_ft.bqschema"
)
DEFAULT_OUTPUT_DB = DEFAULT_INPUT_DIR / "staging_offres_ft.sqlite"
DEFAULT_TABLE_NAME = "staging_offres_ft"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Charge des offres France Travail NDJSON dans une base SQLite."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Fichier NDJSON ou dossier contenant des fichiers *.ndjson.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Schema BigQuery JSON utilise pour creer la table SQLite.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_OUTPUT_DB,
        help="Chemin de la base SQLite a creer ou mettre a jour.",
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE_NAME,
        help="Nom de la table cible.",
    )
    return parser.parse_args()


def load_schema(schema_path: Path) -> list[dict[str, Any]]:
    with schema_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sqlite_type(bigquery_type: str) -> str:
    return {
        "BOOL": "INTEGER",
        "FLOAT64": "REAL",
        "INT64": "INTEGER",
        "INTEGER": "INTEGER",
        "JSON": "TEXT",
        "RECORD": "TEXT",
        "STRING": "TEXT",
        "TIMESTAMP": "TEXT",
    }.get(bigquery_type, "TEXT")


def quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def create_table(
    connection: sqlite3.Connection, table_name: str, schema: list[dict[str, Any]]
) -> None:
    column_defs: list[str] = []
    for field in schema:
        column_name = quote_identifier(field["name"])
        column_type = sqlite_type(field["type"])
        not_null = " NOT NULL" if field.get("mode") == "REQUIRED" else ""
        primary_key = " PRIMARY KEY" if field["name"] == "id" else ""
        column_defs.append(f"{column_name} {column_type}{not_null}{primary_key}")

    ddl = (
        f"CREATE TABLE IF NOT EXISTS {quote_identifier(table_name)} "
        f"({', '.join(column_defs)})"
    )
    connection.execute(ddl)


def iter_input_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(path for path in input_path.iterdir() if path.suffix == ".ndjson")
    raise FileNotFoundError(f"Chemin introuvable: {input_path}")


def normalize_value(field_type: str, value: Any) -> Any:
    if value is None:
        return None
    if field_type == "BOOL":
        return int(bool(value))
    if field_type in {"JSON", "RECORD"}:
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def build_row(record: dict[str, Any], schema: list[dict[str, Any]]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for field in schema:
        field_name = field["name"]
        value = record.get(field_name)
        row[field_name] = normalize_value(field["type"], value)
    return row


def insert_rows(
    connection: sqlite3.Connection,
    table_name: str,
    schema: list[dict[str, Any]],
    input_files: list[Path],
) -> int:
    columns = [field["name"] for field in schema]
    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(quote_identifier(column) for column in columns)
    sql = (
        f"INSERT OR REPLACE INTO {quote_identifier(table_name)} "
        f"({quoted_columns}) VALUES ({placeholders})"
    )

    inserted_rows = 0
    for input_file in input_files:
        with input_file.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"JSON invalide dans {input_file} ligne {line_number}"
                    ) from exc

                row = build_row(record, schema)
                values = [row[column] for column in columns]
                connection.execute(sql, values)
                inserted_rows += 1

    return inserted_rows


def main() -> None:
    args = parse_args()
    schema = load_schema(args.schema)
    input_files = iter_input_files(args.input)

    args.db.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(args.db) as connection:
        create_table(connection, args.table, schema)
        inserted_rows = insert_rows(connection, args.table, schema, input_files)
        connection.commit()

    print(
        f"{inserted_rows} lignes chargees dans {args.db} "
        f"(table {args.table}, schema {args.schema.name}, {len(input_files)} fichier(s))."
    )


if __name__ == "__main__":
    main()
