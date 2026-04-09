import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_OFFERS_DIR = (
    Path(__file__).resolve().parent.parent
    / "02_extract"
    / "data"
    / "france_travail_offres"
)
DEFAULT_REFERENTIALS_DIR = (
    Path(__file__).resolve().parent.parent
    / "02_extract"
    / "data"
    / "france_travail_referentiels"
)
DEFAULT_OUTPUT_MD = (
    Path(__file__).resolve().parent / "france_travail_offer_schema.md"
)
DEFAULT_OUTPUT_JSON = (
    Path(__file__).resolve().parent / "france_travail_offer_schema.json"
)

TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

REFERENTIAL_HINTS = {
    "romeCode": ("ref_metiers_rome", "code"),
    "romeLibelle": ("ref_metiers_rome", "libelle"),
    "typeContrat": ("ref_types_contrats", "code"),
    "typeContratLibelle": ("ref_types_contrats", "libelle"),
    "secteurActivite": ("ref_secteurs_activites", "code"),
    "secteurActiviteLibelle": ("ref_secteurs_activites", "libelle"),
    "langues[].libelle": ("ref_langues", "libelle"),
    "permis[].libelle": ("ref_permis", "libelle"),
    "formations[].niveauLibelle": ("ref_niveaux_formations", "libelle"),
}


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
        return "timestamp_str" if TIMESTAMP_RE.match(value) else "str"
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
        return text[:120] + ("..." if len(text) > 120 else "")
    return str(value)


def suggest_bq_type(observed_types: set[str]) -> str:
    non_null_types = observed_types - {"null"}

    if not non_null_types:
        return "STRING"
    if non_null_types == {"bool"}:
        return "BOOL"
    if non_null_types == {"int"}:
        return "INT64"
    if non_null_types <= {"int", "float"}:
        return "FLOAT64"
    if non_null_types == {"timestamp_str"}:
        return "TIMESTAMP"
    if non_null_types == {"dict"}:
        return "JSON"
    if non_null_types == {"list"}:
        return "JSON"
    if "dict" in non_null_types or "list" in non_null_types:
        return "JSON"
    return "STRING"


@dataclass
class FieldStats:
    occurrences: int = 0
    non_null_occurrences: int = 0
    types: set[str] = field(default_factory=set)
    examples: list[str] = field(default_factory=list)
    distinct_values: set[str] = field(default_factory=set)

    def register(self, value: Any) -> None:
        self.occurrences += 1
        value_type = infer_type(value)
        self.types.add(value_type)

        if value is not None:
            self.non_null_occurrences += 1

        if value_type not in {"dict", "list", "null"}:
            example = format_scalar(value)
            if len(self.examples) < 3 and example not in self.examples:
                self.examples.append(example)
            if len(self.distinct_values) < 500:
                self.distinct_values.add(str(value))


def load_offers_from_file(file_path: Path) -> list[dict[str, Any]]:
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
                raise ValueError(f"Chaque ligne de {file_path} doit etre un objet JSON.")
            offers.append(payload)
    return offers


def load_referentials(directory: Path) -> dict[str, dict[str, set[str]]]:
    referentials: dict[str, dict[str, set[str]]] = {}
    for file_path in sorted(directory.glob("*.json")):
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else []
        values_by_key: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            if not isinstance(row, dict):
                continue
            for key, value in row.items():
                if value is None or isinstance(value, (dict, list)):
                    continue
                values_by_key[key].add(str(value))
        referentials[file_path.stem] = dict(values_by_key)
    return referentials


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


def compute_referential_match(
    field_path: str,
    field_stats: FieldStats,
    referentials: dict[str, dict[str, set[str]]],
) -> tuple[str | None, float | None]:
    hint = REFERENTIAL_HINTS.get(field_path)
    if not hint:
        return None, None

    referential_name, key = hint
    ref_values = referentials.get(referential_name, {}).get(key, set())
    if not ref_values or not field_stats.distinct_values:
        return f"{referential_name}.{key}", None

    matched = sum(1 for value in field_stats.distinct_values if value in ref_values)
    coverage = round((matched / len(field_stats.distinct_values)) * 100, 2)
    return f"{referential_name}.{key}", coverage


def build_rows(
    offer_count: int,
    stats_by_path: dict[str, FieldStats],
    referentials: dict[str, dict[str, set[str]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field_path in sorted(stats_by_path):
        field_stats = stats_by_path[field_path]
        presence_rate = (
            round((field_stats.occurrences / offer_count) * 100, 2)
            if offer_count
            else 0.0
        )
        referential, ref_coverage = compute_referential_match(
            field_path, field_stats, referentials
        )
        rows.append(
            {
                "field_path": field_path,
                "presence_count": field_stats.occurrences,
                "non_null_count": field_stats.non_null_occurrences,
                "presence_rate_pct": presence_rate,
                "observed_types": sorted(field_stats.types),
                "suggested_bigquery_type": suggest_bq_type(field_stats.types),
                "examples": field_stats.examples,
                "referential": referential,
                "referential_match_pct_on_distinct_values": ref_coverage,
            }
        )
    return rows


def render_markdown(
    rows: list[dict[str, Any]],
    offer_count: int,
    offer_files: list[Path],
    referentials: dict[str, dict[str, set[str]]],
) -> str:
    top_level_rows = [row for row in rows if "." not in row["field_path"] and "[]" not in row["field_path"]]

    lines = [
        "# Schema des offres France Travail",
        "",
        "## Resume",
        "",
        f"- Offres analysees : `{offer_count}`",
        f"- Fichiers offres : `{len(offer_files)}`",
        f"- Champs detectes : `{len(rows)}`",
        f"- Referentiels charges : `{len(referentials)}`",
        "",
        "## Fichiers utilises",
        "",
    ]
    lines.extend(f"- `{file_path}`" for file_path in offer_files)
    lines.extend(
        [
            "",
            "## Referentiels charges",
            "",
        ]
    )
    lines.extend(
        f"- `{name}` : {', '.join(sorted(values_by_key))}"
        for name, values_by_key in sorted(referentials.items())
    )
    lines.extend(
        [
            "",
            "## Champs top-level",
            "",
            "| Champ | Presence % | Types | BigQuery | Referential | Exemples |",
            "| --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in top_level_rows:
        examples = " / ".join(row["examples"]) if row["examples"] else ""
        referential = row["referential"] or ""
        lines.append(
            f"| `{row['field_path']}` | {row['presence_rate_pct']:.2f} | "
            f"`{', '.join(row['observed_types'])}` | `{row['suggested_bigquery_type']}` | "
            f"`{referential}` | {examples} |"
        )

    lines.extend(
        [
            "",
            "## Inventaire complet des champs",
            "",
            "| Champ | Presence % | Non null | Types | BigQuery | Referential | Couverture ref % | Exemples |",
            "| --- | ---: | ---: | --- | --- | --- | ---: | --- |",
        ]
    )
    for row in rows:
        examples = " / ".join(row["examples"]) if row["examples"] else ""
        referential = row["referential"] or ""
        coverage = (
            f"{row['referential_match_pct_on_distinct_values']:.2f}"
            if row["referential_match_pct_on_distinct_values"] is not None
            else ""
        )
        lines.append(
            f"| `{row['field_path']}` | {row['presence_rate_pct']:.2f} | "
            f"{row['non_null_count']} | `{', '.join(row['observed_types'])}` | "
            f"`{row['suggested_bigquery_type']}` | `{referential}` | {coverage} | "
            f"{examples} |"
        )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Construit un schema observe des offres France Travail et le rapproche "
            "des referentiels telecharges localement."
        )
    )
    parser.add_argument(
        "--offers-dir",
        type=Path,
        default=DEFAULT_OFFERS_DIR,
        help=f"Dossier des offres FT (defaut: {DEFAULT_OFFERS_DIR})",
    )
    parser.add_argument(
        "--referentials-dir",
        type=Path,
        default=DEFAULT_REFERENTIALS_DIR,
        help=f"Dossier des referentiels FT (defaut: {DEFAULT_REFERENTIALS_DIR})",
    )
    parser.add_argument(
        "--pattern",
        default="offres_data_market_*.ndjson",
        help="Pattern de fichiers offres a analyser.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help=f"Chemin du rapport Markdown (defaut: {DEFAULT_OUTPUT_MD})",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help=f"Chemin du rapport JSON (defaut: {DEFAULT_OUTPUT_JSON})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    offer_files = sorted(args.offers_dir.glob(args.pattern))
    if not offer_files:
        raise FileNotFoundError(
            f"Aucun fichier offre ne correspond a '{args.pattern}' dans {args.offers_dir}"
        )

    referentials = load_referentials(args.referentials_dir)
    offer_count, stats_by_path = analyze_offers(offer_files)
    rows = build_rows(offer_count, stats_by_path, referentials)

    args.output_json.write_text(
        json.dumps(
            {
                "offer_count": offer_count,
                "offer_files": [str(path) for path in offer_files],
                "referentials": sorted(referentials),
                "fields": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    args.output_md.write_text(
        render_markdown(rows, offer_count, offer_files, referentials),
        encoding="utf-8",
    )

    print(f"Offres analysees : {offer_count}")
    print(f"Champs detectes  : {len(rows)}")
    print(f"Rapport Markdown : {args.output_md}")
    print(f"Rapport JSON     : {args.output_json}")


if __name__ == "__main__":
    main()
