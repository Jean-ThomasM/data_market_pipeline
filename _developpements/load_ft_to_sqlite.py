import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "02_extract"
    / "data"
    / "france_travail_offres"
)
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "france_travail_explore.sqlite"


def load_offers_from_file(file_path: Path) -> list[dict[str, Any]]:
    if file_path.suffix == ".ndjson":
        offers: list[dict[str, Any]] = []
        with file_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Ligne NDJSON invalide dans {file_path}:{line_number}: {exc}"
                    ) from exc
                if not isinstance(payload, dict):
                    raise ValueError(
                        f"Chaque ligne de {file_path} doit etre un objet JSON."
                    )
                offers.append(payload)
        return offers

    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict) and "resultats" in payload:
        results = payload["resultats"]
        if not isinstance(results, list):
            raise ValueError(f"La cle 'resultats' de {file_path} doit etre une liste.")
        return [item for item in results if isinstance(item, dict)]

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    raise ValueError(
        f"Structure JSON non supportee dans {file_path}. Attendu: liste ou objet avec 'resultats'."
    )


def flatten_offer(payload: dict[str, Any], parent_key: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}

    for key, value in payload.items():
        flat_key = f"{parent_key}.{key}" if parent_key else key

        if isinstance(value, dict):
            flat.update(flatten_offer(value, flat_key))
            continue

        if isinstance(value, list):
            flat[flat_key] = json.dumps(value, ensure_ascii=False)
            continue

        flat[flat_key] = value

    return flat


def sqlite_column_name(field_name: str) -> str:
    return field_name.replace(".", "__").replace("-", "_")


def sqlite_declared_type(values: list[Any]) -> str:
    non_null_values = [value for value in values if value is not None]
    if not non_null_values:
        return "TEXT"
    if all(isinstance(value, bool) for value in non_null_values):
        return "INTEGER"
    if all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in non_null_values
    ):
        return "INTEGER"
    if all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in non_null_values
    ):
        return "REAL"
    return "TEXT"


def sqlite_value(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    return value


def build_flat_schema(
    flattened_offers: list[dict[str, Any]],
) -> list[tuple[str, str, str]]:
    values_by_field: dict[str, list[Any]] = {}

    for offer in flattened_offers:
        for field_name, value in offer.items():
            values_by_field.setdefault(field_name, []).append(value)

    schema: list[tuple[str, str, str]] = []
    for field_name in sorted(values_by_field):
        schema.append(
            (
                field_name,
                sqlite_column_name(field_name),
                sqlite_declared_type(values_by_field[field_name]),
            )
        )
    return schema


def create_raw_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS raw_ft_offres_json")
    conn.execute(
        """
        CREATE TABLE raw_ft_offres_json (
            offer_id TEXT,
            source_file TEXT NOT NULL,
            raw_json TEXT NOT NULL
        )
        """
    )


def create_flat_table(
    conn: sqlite3.Connection,
    schema: list[tuple[str, str, str]],
) -> None:
    conn.execute("DROP TABLE IF EXISTS stg_ft_offres_flat")

    columns_sql = [
        '"offer_id" TEXT',
        '"source_file" TEXT NOT NULL',
        '"raw_json" TEXT NOT NULL',
    ]
    for _, column_name, declared_type in schema:
        columns_sql.append(f'"{column_name}" {declared_type}')

    conn.execute(f"CREATE TABLE stg_ft_offres_flat ({', '.join(columns_sql)})")


def create_field_catalog_table(
    conn: sqlite3.Connection,
    schema: list[tuple[str, str, str]],
    flattened_offers: list[dict[str, Any]],
) -> None:
    conn.execute("DROP TABLE IF EXISTS field_catalog")
    conn.execute(
        """
        CREATE TABLE field_catalog (
            field_path TEXT NOT NULL,
            sqlite_column TEXT NOT NULL,
            sqlite_type TEXT NOT NULL,
            presence_count INTEGER NOT NULL,
            example_value TEXT
        )
        """
    )

    rows = []
    for field_path, column_name, declared_type in schema:
        presence_count = sum(1 for offer in flattened_offers if field_path in offer)
        example_value = next(
            (
                str(value).replace("\n", "\\n")[:200]
                for offer in flattened_offers
                for key, value in offer.items()
                if key == field_path and value is not None
            ),
            None,
        )
        rows.append(
            (field_path, column_name, declared_type, presence_count, example_value)
        )

    conn.executemany(
        """
        INSERT INTO field_catalog (
            field_path,
            sqlite_column,
            sqlite_type,
            presence_count,
            example_value
        ) VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )


def insert_rows(
    conn: sqlite3.Connection,
    raw_rows: list[tuple[str | None, str, str]],
    flattened_offers: list[dict[str, Any]],
    source_files: list[str],
    schema: list[tuple[str, str, str]],
) -> None:
    conn.executemany(
        "INSERT INTO raw_ft_offres_json (offer_id, source_file, raw_json) VALUES (?, ?, ?)",
        raw_rows,
    )

    flat_column_names = ["offer_id", "source_file", "raw_json"] + [
        column_name for _, column_name, _ in schema
    ]
    placeholders = ", ".join("?" for _ in flat_column_names)

    values_to_insert = []
    for raw_row, offer, source_file in zip(
        raw_rows,
        flattened_offers,
        source_files,
        strict=True,
    ):
        raw_json = raw_row[2]
        row = [offer.get("id"), source_file, raw_json]
        for field_path, _, _ in schema:
            row.append(sqlite_value(offer.get(field_path)))
        values_to_insert.append(tuple(row))

    quoted_columns = ", ".join(f'"{name}"' for name in flat_column_names)
    conn.executemany(
        f"INSERT INTO stg_ft_offres_flat ({quoted_columns}) VALUES ({placeholders})",
        values_to_insert,
    )


def build_database(files: list[Path], db_path: Path) -> tuple[int, int]:
    raw_rows: list[tuple[str | None, str, str]] = []
    flattened_offers: list[dict[str, Any]] = []
    source_files: list[str] = []

    for file_path in files:
        offers = load_offers_from_file(file_path)
        for offer in offers:
            raw_rows.append(
                (
                    offer.get("id"),
                    file_path.name,
                    json.dumps(offer, ensure_ascii=False),
                )
            )
            flattened_offers.append(flatten_offer(offer))
            source_files.append(file_path.name)

    schema = build_flat_schema(flattened_offers)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        create_raw_table(conn)
        create_flat_table(conn, schema)
        insert_rows(conn, raw_rows, flattened_offers, source_files, schema)
        create_field_catalog_table(conn, schema, flattened_offers)
        conn.commit()
    finally:
        conn.close()

    return len(flattened_offers), len(schema)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Charge les offres France Travail locales dans une base SQLite pour exploration via DBeaver."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Dossier des offres locales (defaut: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--pattern",
        default="offres_data_market_*",
        help="Pattern de fichiers a charger.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Chemin de la base SQLite cible (defaut: {DEFAULT_DB_PATH})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    files = sorted(args.data_dir.glob(args.pattern))

    if not files:
        raise FileNotFoundError(
            f"Aucun fichier ne correspond a '{args.pattern}' dans {args.data_dir}"
        )

    offer_count, field_count = build_database(files, args.db_path)

    print(f"Base SQLite creee : {args.db_path}")
    print(f"Fichiers charges   : {len(files)}")
    print(f"Offres chargees    : {offer_count}")
    print(f"Champs aplatis     : {field_count}")
    print("Tables disponibles : raw_ft_offres_json, stg_ft_offres_flat, field_catalog")


if __name__ == "__main__":
    main()
