#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


SOURCE_COLUMNS = {
    "siren": "siren",
    "siret": "siret",
    "denominationUniteLegale": "denomination_unite_legale",
    "activitePrincipaleNAF25Etablissement": "NAF",
}
DEFAULT_CHUNK_SIZE = 20000


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_nullable_string(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return "NULL"
    return sql_quote(stripped)


def iter_csv_files(input_dir: Path):
    for path in sorted(input_dir.glob("*.csv")):
        if path.is_file():
            yield path


def validate_headers(fieldnames, csv_path: Path):
    if fieldnames is None:
        raise ValueError(f"{csv_path} has no CSV header")
    missing = [name for name in SOURCE_COLUMNS if name not in fieldnames]
    if missing:
        raise ValueError(f"{csv_path} missing columns: {', '.join(missing)}")


def generate_insert_files(input_dir: Path, output_path: Path, chunk_size: int):
    if chunk_size <= 0:
        raise ValueError("--chunk-size must be > 0")

    rows_written = 0
    files_written = 0
    rows_in_current_file = 0
    current_file_index = 1
    current_output = None

    def output_for(index: int) -> Path:
        return output_path.with_name(f"{output_path.stem}_{index:04d}{output_path.suffix}")

    def open_next_file():
        nonlocal current_output, files_written, current_file_index, rows_in_current_file
        if current_output is not None:
            current_output.close()
        path = output_for(current_file_index)
        current_output = path.open("w", encoding="utf-8", newline="\n")
        current_file_index += 1
        files_written += 1
        rows_in_current_file = 0

    open_next_file()
    try:
        for csv_path in iter_csv_files(input_dir):
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle, delimiter=",")
                validate_headers(reader.fieldnames, csv_path)
                for row in reader:
                    if rows_in_current_file >= chunk_size:
                        open_next_file()
                    siren = sql_quote((row.get("siren") or "").strip())
                    siret = sql_quote((row.get("siret") or "").strip())
                    denomination = sql_nullable_string(
                        row.get("denominationUniteLegale") or ""
                    )
                    naf = sql_nullable_string(
                        row.get("activitePrincipaleNAF25Etablissement") or ""
                    )
                    current_output.write(
                        "INSERT INTO entreprises "
                        "(siren, siret, denomination_unite_legale, NAF) "
                        f"VALUES ({siren}, {siret}, {denomination}, {naf});\n"
                    )
                    rows_written += 1
                    rows_in_current_file += 1
    finally:
        if current_output is not None:
            current_output.close()

    return rows_written, files_written


def main():
    parser = argparse.ArgumentParser(
        description="Generate insert.sql from all CSV files in this directory."
    )
    parser.add_argument(
        "--input-dir",
        default=Path(__file__).resolve().parent,
        type=Path,
        help="Directory containing source CSV files (default: script directory).",
    )
    parser.add_argument(
        "--output",
        default=None,
        type=Path,
        help="Base output SQL file path (default: <input-dir>/insert.sql).",
    )
    parser.add_argument(
        "--chunk-size",
        default=DEFAULT_CHUNK_SIZE,
        type=int,
        help=f"Maximum INSERT statements per SQL file (default: {DEFAULT_CHUNK_SIZE}).",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_path = args.output.resolve() if args.output else input_dir / "insert.sql"

    rows, files = generate_insert_files(input_dir, output_path, args.chunk_size)
    first_output = output_path.with_name(
        f"{output_path.stem}_{1:04d}{output_path.suffix}"
    )
    print(
        f"Generated {files} file(s) from {first_output} with {rows} INSERT statements "
        f"({args.chunk_size} max per file)."
    )


if __name__ == "__main__":
    main()
