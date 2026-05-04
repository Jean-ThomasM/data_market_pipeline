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


def generate_insert_file(input_dir: Path, output_path: Path) -> int:
    rows_written = 0
    with output_path.open("w", encoding="utf-8", newline="\n") as out:
        for csv_path in iter_csv_files(input_dir):
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle, delimiter=",")
                validate_headers(reader.fieldnames, csv_path)
                for row in reader:
                    siren = sql_quote((row.get("siren") or "").strip())
                    siret = sql_quote((row.get("siret") or "").strip())
                    denomination = sql_nullable_string(
                        row.get("denominationUniteLegale") or ""
                    )
                    naf = sql_nullable_string(
                        row.get("activitePrincipaleNAF25Etablissement") or ""
                    )
                    out.write(
                        "INSERT INTO entreprises "
                        "(siren, siret, denomination_unite_legale, NAF) "
                        f"VALUES ({siren}, {siret}, {denomination}, {naf});\n"
                    )
                    rows_written += 1
    return rows_written


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
        help="Output SQL file path (default: <input-dir>/insert.sql).",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_path = args.output.resolve() if args.output else input_dir / "insert.sql"

    rows = generate_insert_file(input_dir, output_path)
    print(f"Generated {output_path} with {rows} INSERT statements.")


if __name__ == "__main__":
    main()
