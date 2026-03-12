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


@dataclass
class GeoOutputPaths:
    """Chemins de sortie pour les fichiers transformés."""

    regions: Path
    departements: Path
    communes: Path
    communes_codes_postaux: Path
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


def _dump_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    """
    Écrit un fichier CSV simple avec en-têtes, séparateur `,`
    et encodage UTF-8.
    """
    import csv

    if not rows:
        # On écrit quand même le fichier vide avec aucun enregistrement.
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            f.write("")
        return

    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_geo_paths(input_dir: Path, output_dir: Path) -> tuple[GeoInputPaths, GeoOutputPaths]:
    """
    Construit les objets de chemins d'entrée/sortie à partir des dossiers.
    """
    in_paths = GeoInputPaths(
        regions=input_dir / "regions.json",
        departements=input_dir / "departements.json",
        communes=input_dir / "communes.json",
        epcis=(input_dir / "epcis.json"),
    )

    out_paths = GeoOutputPaths(
        regions=output_dir / "regions.csv",
        departements=output_dir / "departements.csv",
        communes=output_dir / "communes.csv",
        communes_codes_postaux=output_dir / "communes_codes_postaux.csv",
        epcis=output_dir / "epcis.csv",
    )
    return in_paths, out_paths


def run_geo_transformation(
    input_dir: str = "data/data_geo",
    output_dir: str = "data/processed_geo",
) -> None:
    """
    Charge les JSON géographiques depuis `input_dir`, applique les
    transformations de nettoyage/typage et écrit des CSV prêts pour
    la couche de staging SQL dans `output_dir`.
    """
    input_base = Path(input_dir)
    output_base = Path(output_dir)

    print(f"[geo] Démarrage de la transformation JSON -> CSV")
    print(f"[geo] Dossier d'entrée : {input_base.resolve()}")
    print(f"[geo] Dossier de sortie : {output_base.resolve()}")

    _ensure_output_dir(output_base)
    in_paths, out_paths = build_geo_paths(input_base, output_base)

    # Chargement des données brutes
    print("[geo] Chargement des JSON géographiques...")
    regions_raw = _load_json(in_paths.regions)
    departements_raw = _load_json(in_paths.departements)
    communes_raw = _load_json(in_paths.communes)

    epcis_raw: Optional[List[Dict[str, Any]]] = None
    if in_paths.epcis and in_paths.epcis.exists():
        epcis_raw = _load_json(in_paths.epcis)

    # Transformations
    print("[geo] Transformations en tables normalisées...")
    regions = _transform_regions(regions_raw)
    departements = _transform_departements(departements_raw)
    communes = _transform_communes(communes_raw)
    communes_codes_postaux = _explode_commune_codes_postaux(communes_raw)
    epcis: List[Dict[str, Any]] = []
    if epcis_raw is not None:
        epcis = _transform_epcis(epcis_raw)

    # Écriture des fichiers
    print("[geo] Écriture des CSV dans le dossier de sortie...")
    _dump_csv(regions, out_paths.regions)
    print(f"[geo]   - regions.csv : {len(regions)} lignes")
    _dump_csv(departements, out_paths.departements)
    print(f"[geo]   - departements.csv : {len(departements)} lignes")
    _dump_csv(communes, out_paths.communes)
    print(f"[geo]   - communes.csv : {len(communes)} lignes")
    _dump_csv(communes_codes_postaux, out_paths.communes_codes_postaux)
    print(f"[geo]   - communes_codes_postaux.csv : {len(communes_codes_postaux)} lignes")
    if epcis:
        _dump_csv(epcis, out_paths.epcis)  # type: ignore[arg-type]
        print(f"[geo]   - epcis.csv : {len(epcis)} lignes")

    print("[geo] Transformation JSON -> CSV terminée.")


if __name__ == "__main__":
    run_geo_transformation()

