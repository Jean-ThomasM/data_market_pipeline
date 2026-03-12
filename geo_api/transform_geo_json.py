import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class GeoInputPaths:
    """Chemins d'entrée pour les fichiers JSON bruts."""

    regions: Path
    departements: Path
    communes: Path
    epcis: Optional[Path] = None




def _load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier JSON introuvable: {path}")
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, list):
        raise ValueError(f"Le fichier JSON {path} doit contenir une liste d'objets.")
    return obj


def _ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _normalise_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _safe_int(value: Any) -> Optional[int]:
    if value in (None, "", " "):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _explode_commune_codes_postaux(
    communes: Iterable[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    À partir de la structure brute des communes, produit une table à un
    enregistrement par couple (commune_code, code_postal).
    """
    rows: List[Dict[str, Any]] = []
    for c in communes:
        code_commune = _normalise_str(c.get("code"))
        if not code_commune:
            continue
        codes_postaux = c.get("codesPostaux") or []
        if not isinstance(codes_postaux, list):
            codes_postaux = [codes_postaux]
        for cp in codes_postaux:
            cp_norm = _normalise_str(cp)
            if not cp_norm:
                continue
            rows.append(
                {
                    "commune_code": code_commune,
                    "code_postal": cp_norm,
                }
            )
    return rows


def _transform_regions(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for r in raw:
        code = _normalise_str(r.get("code"))
        nom = _normalise_str(r.get("nom"))
        if not code:
            continue
        rows.append(
            {
                "region_code": code,
                "region_nom": nom,
            }
        )
    return rows


def _transform_departements(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for d in raw:
        code = _normalise_str(d.get("code"))
        nom = _normalise_str(d.get("nom"))
        code_region = _normalise_str(d.get("codeRegion"))
        if not code:
            continue
        rows.append(
            {
                "departement_code": code,
                "departement_nom": nom,
                "region_code": code_region,
            }
        )
    return rows


def _transform_communes(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for c in raw:
        code_commune = _normalise_str(c.get("code"))
        if not code_commune:
            continue
        rows.append(
            {
                "commune_code": code_commune,
                "commune_nom": _normalise_str(c.get("nom")),
                "departement_code": _normalise_str(c.get("codeDepartement")),
                "region_code": _normalise_str(c.get("codeRegion")),
                "population": _safe_int(c.get("population")),
            }
        )
    return rows


def _transform_epcis(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for e in raw:
        code = _normalise_str(e.get("code"))
        if not code:
            continue
        rows.append(
            {
                "epci_code": code,
                "epci_nom": _normalise_str(e.get("nom")),
                "region_code": _normalise_str(e.get("codeRegion")),
                "nature": _normalise_str(e.get("nature")),
            }
        )
    return rows


@dataclass
class GeoOutputPaths:
    """
    (Obsolète) Ancien schéma de sorties CSV.
    Conservé uniquement pour compatibilité potentielle, mais
    la génération de CSV n'est plus utilisée dans le pipeline.
    """

    regions: Path
    departements: Path
    communes: Path
    communes_codes_postaux: Path
    epcis: Optional[Path] = None

