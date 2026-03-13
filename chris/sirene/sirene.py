from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "StockUniteLegale_utf8.parquet"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "sirenes"
OutputFormat = Literal["csv", "parquet"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split one parquet file into multiple output files in "
            "chris/sirene/sirenes."
        )
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help=f"Source parquet file (default: {DEFAULT_INPUT}).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Target output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--rows-per-file",
        type=int,
        default=200_000,
        help="Maximum number of rows per output file.",
    )
    parser.add_argument(
        "--prefix",
        default="sirene_part",
        help="Output filename prefix.",
    )
    parser.add_argument(
        "--output-format",
        choices=["csv", "parquet"],
        default="csv",
        help="Output file format (default: csv).",
    )
    return parser.parse_args()


def split_parquet(
    input_path: Path,
    output_dir: Path,
    rows_per_file: int,
    prefix: str,
    output_format: OutputFormat,
) -> tuple[int, int]:
    try:
        import pyarrow as pa
        import pyarrow.csv as pcsv
        import pyarrow.parquet as pq
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: pyarrow. Install it with: uv add pyarrow"
        ) from exc

    if rows_per_file <= 0:
        raise ValueError("--rows-per-file must be > 0")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_file = pq.ParquetFile(input_path)
    total_rows = 0
    file_count = 0

    for file_count, batch in enumerate(
        parquet_file.iter_batches(batch_size=rows_per_file), start=1
    ):
        table = pa.Table.from_batches([batch])
        extension = "csv" if output_format == "csv" else "parquet"
        output_path = output_dir / f"{prefix}_{file_count:06d}.{extension}"
        if output_format == "csv":
            pcsv.write_csv(table, output_path)
        else:
            pq.write_table(table, output_path, compression="snappy")
        total_rows += table.num_rows
        print(f"Wrote {output_path} ({table.num_rows} rows)")

    return file_count, total_rows


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    file_count, total_rows = split_parquet(
        input_path=input_path,
        output_dir=output_dir,
        rows_per_file=args.rows_per_file,
        prefix=args.prefix,
        output_format=args.output_format,
    )
    print(f"Done. Generated {file_count} files for {total_rows} rows.")


if __name__ == "__main__":
    main()
