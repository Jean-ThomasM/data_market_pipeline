import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


WEBHOOK_URL = "https://n8n.carthographie.fr/webhook/e35588dd-bf2c-4183-952a-2694ef4a0b95"


def call_n8n_webhook(label: str, siren: str) -> dict:
    query = urlencode(
        {
            "denomination_unite_legales": label,
            "siren": siren,
        }
    )
    url = f"{WEBHOOK_URL}?{query}"

    try:
        with urlopen(url, timeout=30) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(f"Erreur HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Erreur reseau: {exc.reason}") from exc

    return json.loads(body)


def format_value(value: object) -> str:
    if value is None:
        return "null"
    return str(value)


def print_result(result: dict) -> None:
    for key, value in result.items():
        if isinstance(value, list):
            print(f"{key}:")
            for index, item in enumerate(value, start=1):
                if isinstance(item, dict):
                    print(f"  {index}.")
                    for item_key, item_value in item.items():
                        print(f"     {item_key}: {format_value(item_value)}")
                else:
                    print(f"  {index}. {format_value(item)}")
        elif isinstance(value, dict):
            print(f"{key}:")
            for item_key, item_value in value.items():
                print(f"  {item_key}: {format_value(item_value)}")
        else:
            print(f"{key}: {format_value(value)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Appelle le webhook n8n avec un label et un SIREN.")
    parser.add_argument("label", help="Valeur du parametre denomination_unite_legales")
    parser.add_argument("siren", help="Valeur du parametre siren")
    args = parser.parse_args()

    result = call_n8n_webhook(args.label, args.siren)
    print_result(result)


if __name__ == "__main__":
    main()
