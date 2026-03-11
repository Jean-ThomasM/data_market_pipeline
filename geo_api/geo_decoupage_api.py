import json
from pathlib import Path
from typing import List, Dict, Any
import os
import requests
from dotenv import load_dotenv
load_dotenv()
BASE_URL = os.getenv("GEO_API_URL")


def _get(path: str, **params: Any) -> Any:
    """
    Appelle l'API geo.api.gouv.fr avec gestion simple des erreurs.
    """
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=15)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f"Erreur API {url} - {resp.status_code}: {resp.text[:200]}") from exc
    return resp.json()

def get_regions() -> List[Dict[str, Any]]:
    """
    Renvoie la liste des régions.
    Structure exemple:
    [
      {"code": "84", "nom": "Auvergne-Rhône-Alpes"},
      ...
    ]
    """
    return _get("/regions")


def get_departements() -> List[Dict[str, Any]]:
    """
    Renvoie la liste de tous les départements.
    Structure exemple:
    [
      {"code": "69", "nom": "Rhône", "codeRegion": "84"},
      ...
    ]
    """
    return _get("/departements")

def get_communes(fields: str | None = None) -> List[Dict[str, Any]]:
    """
    Renvoie la liste de toutes les communes de France.

    :param fields: liste de champs à renvoyer, séparés par des virgules
                   (ex: "code,nom,codeRegion,codeDepartement,codesPostaux,population").
    """
    params: Dict[str, Any] = {}
    if fields:
        params["fields"] = fields
    return _get("/communes", **params)


def get_epcis() -> List[Dict[str, Any]]:
    """
    Renvoie la liste de tous les EPCI.
    Structure exemple:
    [
      {"code": "200046977", "nom": "Métropole de Lyon", "codeRegion": "84", "nature": "METROPOLE"},
      ...
    ]
    """
    return _get("/epcis")


def export_geo_to_json(output_dir) -> None:
    """
    Extrait les données géographiques (régions, départements, communes)
    et les enregistre dans 3 fichiers JSON distincts dans un dossier.
    Si le script est relancé, les fichiers sont écrasés.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Récupération des régions...")
    regions = get_regions()

    print("Récupération des départements...")
    departements = get_departements()

    print("Récupération des communes (toutes la France)...")
    communes = get_communes(
        fields="code,nom,codeRegion,codeDepartement,codesPostaux,population"
    )

    def _dump_json(data: List[Dict[str, Any]], filename: str) -> None:
        path = out_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Écrit {len(data)} enregistrements dans {path}")

    _dump_json(regions, "regions.json")
    _dump_json(departements, "departements.json")
    _dump_json(communes, "communes.json")


if __name__ == "__main__":
    # Pour lancer l'extraction directement lorsque le script est exécuté :
    export_geo_to_json()

