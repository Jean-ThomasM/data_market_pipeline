#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${1:-$SCRIPT_DIR}"
OUTPUT_FILE="${2:-$INPUT_DIR/entreprises.csv}"

python3 - "$INPUT_DIR" "$OUTPUT_FILE" <<'PY'
import csv
import sys
from pathlib import Path

input_dir = Path(sys.argv[1]).resolve()
output_file = Path(sys.argv[2]).resolve()

source_columns = {
    "siren": "siren",
    "siret": "siret",
    "denominationUniteLegale": "denomination_unite_legale",
    "activitePrincipaleNAF25Etablissement": "NAF",
}

if not input_dir.is_dir():
    raise SystemExit(f"Input directory does not exist: {input_dir}")

csv_files = [
    p for p in sorted(input_dir.glob("*.csv"))
    if p.is_file() and p.resolve() != output_file
]

if not csv_files:
    raise SystemExit(f"No CSV files found in: {input_dir}")

rows_written = 0
with output_file.open("w", encoding="utf-8", newline="") as out_handle:
    writer = csv.writer(out_handle)
    writer.writerow(["siren", "siret", "denomination_unite_legale", "NAF"])

    for csv_path in csv_files:
        with csv_path.open("r", encoding="utf-8", newline="") as in_handle:
            reader = csv.DictReader(in_handle)
            if reader.fieldnames is None:
                raise SystemExit(f"{csv_path} has no CSV header")

            missing = [name for name in source_columns if name not in reader.fieldnames]
            if missing:
                raise SystemExit(
                    f"{csv_path} missing columns: {', '.join(missing)}"
                )

            for row in reader:
                writer.writerow([
                    (row.get("siren") or "").strip(),
                    (row.get("siret") or "").strip(),
                    (row.get("denominationUniteLegale") or "").strip(),
                    (row.get("activitePrincipaleNAF25Etablissement") or "").strip(),
                ])
                rows_written += 1

print(f"Generated {output_file} with {rows_written} rows.")
PY
