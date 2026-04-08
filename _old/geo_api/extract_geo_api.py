import json
from pathlib import Path
from typing import List, Dict, Any
import os
import requests

BASE_URL = os.getenv("GEO_API_URL", "https://geo.api.gouv.fr")


def _get(path: str, **params: Any) -> Any:
    """
    Appelle l'API geo.api.gouv.fr avec gestion simple des erreurs.
    """
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, params=params, timeout=15)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Erreur API {url} - {resp.status_code}: {resp.text[:200]}"
        ) from exc
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

    :param fields: liste de champs à renvoyer, séparés par des virgules.
                   Par défaut on récupère exactement :
                   "code,nom,codeRegion,codeDepartement,codesPostaux,population"
                   afin que `codesPostaux` soit toujours présent comme liste
                   complète de codes postaux pour chaque commune.
    """
    # Si aucun `fields` n'est fourni, on force un ensemble de champs
    # cohérent avec nos besoins de pipeline (dont `codesPostaux`).
    return _get("/communes")


def get_epcis() -> List[Dict[str, Any]]:
    """
    Renvoie la liste de tous les EPCI tels que définis par l'API
    geo.api.gouv.fr.

    Structure exemple (simplifiée):
    [
      {
        "code": "200046977",
        "nom": "Métropole de Lyon",
        "codesDepartements": ["69"],
        "codesRegions": ["84"],
        "population": 1417389,
        "type": "METROPOLE"
      },
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
    communes = get_communes()

    print("Récupération des EPCI...")
    epcis = get_epcis()

    def _dump_json(data: List[Dict[str, Any]], filename: str) -> None:
        path = out_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Écrit {len(data)} enregistrements dans {path}")

    _dump_json(regions, "regions.json")
    _dump_json(departements, "departements.json")
    _dump_json(communes, "communes.json")
    _dump_json(epcis, "epcis.json")


if __name__ == "__main__":
    # Pour lancer l'extraction directement lorsque le script est exécuté :
    export_geo_to_json()
