import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "02_extract"
    / "data"
    / "france_travail_offres"
)


def infer_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    return type(value).__name__


def format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        text = value.replace("\n", "\\n").strip()
        return text[:80] + ("..." if len(text) > 80 else "")
    return str(value)


@dataclass
class FieldStats:
    occurrences: int = 0
    non_null_occurrences: int = 0
    types: set[str] = field(default_factory=set)
    examples: list[str] = field(default_factory=list)

    def register(self, value: Any) -> None:
        self.occurrences += 1
        value_type = infer_type(value)
        self.types.add(value_type)

        if value is not None:
            self.non_null_occurrences += 1

        if value_type not in {"dict", "list", "null"} and len(self.examples) < 3:
            example = format_scalar(value)
            if example not in self.examples:
                self.examples.append(example)


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


def walk_value(value: Any, path: str, stats_by_path: dict[str, FieldStats]) -> None:
    stats_by_path[path].register(value)

    if isinstance(value, dict):
        for key, nested_value in value.items():
            nested_path = f"{path}.{key}" if path else key
            walk_value(nested_value, nested_path, stats_by_path)
        return

    if isinstance(value, list):
        item_path = f"{path}[]"
        for item in value:
            walk_value(item, item_path, stats_by_path)


def analyze_offers(files: list[Path]) -> tuple[int, dict[str, FieldStats]]:
    stats_by_path: dict[str, FieldStats] = defaultdict(FieldStats)
    offer_count = 0

    for file_path in files:
        offers = load_offers_from_file(file_path)
        for offer in offers:
            offer_count += 1
            for key, value in offer.items():
                walk_value(value, key, stats_by_path)

    return offer_count, dict(stats_by_path)


def build_report_rows(
    offer_count: int,
    stats_by_path: dict[str, FieldStats],
) -> list[dict[str, str | int | float]]:
    rows: list[dict[str, str | int | float]] = []

    for field_path in sorted(stats_by_path):
        field_stats = stats_by_path[field_path]
        presence_rate = (
            round((field_stats.occurrences / offer_count) * 100, 2)
            if offer_count
            else 0
        )
        rows.append(
            {
                "field_path": field_path,
                "presence_count": field_stats.occurrences,
                "non_null_count": field_stats.non_null_occurrences,
                "presence_rate_pct": presence_rate,
                "types": ", ".join(sorted(field_stats.types)),
                "examples": " | ".join(field_stats.examples),
            }
        )

    return rows


def print_report(rows: list[dict[str, str | int | float]], offer_count: int) -> None:
    print(f"Offres analysees : {offer_count}")
    print(f"Champs detectes  : {len(rows)}")
    print()
    print(
        f"{'field_path':60} {'presence':>8} {'non_null':>8} {'rate%':>8} {'types':25} examples"
    )
    print("-" * 140)

    for row in rows:
        print(
            f"{str(row['field_path'])[:60]:60} "
            f"{int(row['presence_count']):>8} "
            f"{int(row['non_null_count']):>8} "
            f"{float(row['presence_rate_pct']):>8.2f} "
            f"{str(row['types'])[:25]:25} "
            f"{row['examples']}"
        )


def save_json_report(
    output_path: Path, rows: list[dict[str, str | int | float]]
) -> None:
    output_path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Liste tous les champs observes dans les offres France Travail locales."
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
        help="Pattern de fichiers a analyser.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Chemin optionnel pour sauvegarder le rapport en JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    files = sorted(args.data_dir.glob(args.pattern))

    if not files:
        raise FileNotFoundError(
            f"Aucun fichier ne correspond a '{args.pattern}' dans {args.data_dir}"
        )

    offer_count, stats_by_path = analyze_offers(files)
    rows = build_report_rows(offer_count, stats_by_path)
    print_report(rows, offer_count)

    if args.output_json:
        save_json_report(args.output_json, rows)
        print()
        print(f"Rapport JSON ecrit dans : {args.output_json}")


if __name__ == "__main__":
    main()
