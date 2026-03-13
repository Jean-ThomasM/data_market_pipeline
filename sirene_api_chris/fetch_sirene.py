from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

API_BASE_URL = "https://api.insee.fr/api-sirene/3.11/siren"
DEFAULT_OUTPUT_PATH = Path("data/data_sirene/sirene.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch SIRENE data for one SIREN and store the JSON response."
    )
    parser.add_argument("siren", help="Target SIREN (9 digits).")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Output JSON path (default: {DEFAULT_OUTPUT_PATH}).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="INSEE API key (optional if SIRENE_API_KEY or INSEE_API_KEY is set).",
    )
    return parser.parse_args()


def get_api_key(cli_key: str | None) -> str:
    if cli_key:
        return cli_key

    env_key = os.getenv("SIRENE_API_KEY") or os.getenv("INSEE_API_KEY")
    if env_key:
        return env_key

    raise ValueError(
        "Missing API key. Provide --api-key or set SIRENE_API_KEY / INSEE_API_KEY."
    )


def validate_siren(siren: str) -> None:
    if not (siren.isdigit() and len(siren) == 9):
        raise ValueError("SIREN must be exactly 9 digits.")


def fetch_siren_json(siren: str, api_key: str) -> dict:
    url = f"{API_BASE_URL}/{siren}"
    headers = {
        "X-INSEE-Api-Key-Integration": api_key,
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def write_json(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    load_dotenv()
    args = parse_args()

    validate_siren(args.siren)
    api_key = get_api_key(args.api_key)

    data = fetch_siren_json(args.siren, api_key)
    output_path = Path(args.output)
    write_json(data, output_path)

    print(f"SIRENE JSON saved to: {output_path}")


if __name__ == "__main__":
    main()
