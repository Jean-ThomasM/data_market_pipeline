import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Set


def _load_offres_list(path: Path) -> List[Dict[str, Any]]:
    """
    Charge un fichier JSON d'offres France Travail.
    Le format attendu est :
    {
        "metadata": { ... },
        "resultats": [ {offre1}, {offre2}, ... ]
    }
    On renvoie uniquement la liste des offres (clé "resultats").
    """
    if not path.exists():
        raise FileNotFoundError(f"Fichier JSON introuvable : {path}")
    if path.suffix.lower() == ".ndjson":
        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
        return rows

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "resultats" not in data:
        raise ValueError(
            f"Le fichier JSON {path} doit contenir un objet avec une clé 'resultats'."
        )
    resultats = data["resultats"]
    if not isinstance(resultats, list):
        raise ValueError(
            f"La clé 'resultats' du fichier JSON {path} doit contenir une liste d'objets."
        )
    return resultats


def _infer_columns(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Détermine l'ensemble des clés présentes dans la liste d'offres JSON
    afin de créer une table qui reflète la structure du JSON.

    Règles :
    - toutes les clés de premier niveau sont créées telles quelles
    - pour chaque clé dont la valeur est un dictionnaire, on ajoute
      également une colonne aplanie pour chaque sous-clé, de la forme
      "<cle_principale>__<sous_cle>".
    """
    cols: Set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue

        for key, value in row.items():
            # Clé de premier niveau
            cols.add(key)

            # Aplatissement 1 niveau des sous-dictionnaires
            if isinstance(value, dict):
                for sub_key in value.keys():
                    cols.add(f"{key}__{sub_key}")
    return sorted(cols)


def _serialize_value(value: Any) -> str:
    """
    Sérialise une valeur JSON pour stockage en TEXT dans SQLite.
    - scalaires -> str(value)
    - listes / dicts -> json.dumps(value)
    - None -> chaîne vide
    """
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def load_offres_json_to_raw_table(
    conn: sqlite3.Connection, json_path: Path, table_name: str
) -> None:
    """
    Charge le fichier JSON d'offres dans une table SQLite "raw_*" avec
    les mêmes colonnes que le JSON (aucune normalisation).
    """
    if not json_path.exists():
        print(f"[ft-sqlite] Fichier JSON introuvable, ignoré : {json_path}")
        return

    print(
        f"[ft-sqlite] Chargement de {json_path} dans la table {table_name} (offres brutes)..."
    )
    rows = _load_offres_list(json_path)
    if not rows:
        print(f"[ft-sqlite]   Aucune offre dans {json_path}, table non créée.")
        return

    fieldnames = _infer_columns(rows)
    if not fieldnames:
        print(
            f"[ft-sqlite]   Aucune colonne déduite pour {json_path}, table non créée."
        )
        return

    cols_def = ", ".join(f'"{name}" TEXT' for name in fieldnames)

    cur = conn.cursor()
    cur.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    cur.execute(f'CREATE TABLE "{table_name}" ({cols_def})')

    placeholders = ", ".join(["?"] * len(fieldnames))
    to_insert: List[tuple[str, ...]] = []
    for row in rows:
        values: List[str] = []
        for col in fieldnames:
            # Gestion des colonnes aplaties de type "<parent>__<sous_cle>"
            if "__" in col:
                parent, sub_key = col.split("__", 1)
                parent_val = row.get(parent)
                if isinstance(parent_val, dict):
                    raw_val = parent_val.get(sub_key)
                else:
                    raw_val = None
            else:
                raw_val = row.get(col)

            values.append(_serialize_value(raw_val))
        to_insert.append(tuple(values))

    if to_insert:
        cur.executemany(
            f'INSERT INTO "{table_name}" ({", ".join(fieldnames)}) VALUES ({placeholders})',
            to_insert,
        )

    conn.commit()
    print(f"[ft-sqlite]   -> {len(to_insert)} offres insérées dans {table_name}")


def apply_france_travail_views_sql(
    conn: sqlite3.Connection, views_sql_path: Path
) -> None:
    """
    Exécute le fichier SQL de staging des offres France Travail sur la base SQLite.
    """
    if not views_sql_path.exists():
        raise FileNotFoundError(
            f"Fichier SQL de staging introuvable : {views_sql_path}"
        )

    sql = views_sql_path.read_text(encoding="utf-8")
    print(f"[ft-sqlite] Application du SQL de staging depuis {views_sql_path}...")
    conn.executescript(sql)
    conn.commit()
    print("[ft-sqlite] Vues France Travail créées avec succès.")


def main() -> None:
    """
    Charge le dernier fichier brut d'offres France Travail dans SQLite.
    Les transformations SQL sont faites ensuite via dbt.
    """
    db_path = Path("_old/data/geo.sqlite")
    offres_json_dir_candidates = [
        Path("_old/data/france_travail_offres"),
        Path("_old/data/france_travail_offres"),
    ]

    print(f"[ft-sqlite] Base SQLite cible : {db_path.resolve()}")
    def _has_offres_files(path: Path) -> bool:
        return any(path.glob("offres_data_market_*.json")) or any(
            path.glob("offres_data_market_*.ndjson")
        )

    offres_json_dir = next(
        (p for p in offres_json_dir_candidates if p.exists() and _has_offres_files(p)),
        next((p for p in offres_json_dir_candidates if p.exists()), offres_json_dir_candidates[0]),
    )
    print(f"[ft-sqlite] Dossier JSON      : {offres_json_dir.resolve()}")
    if not offres_json_dir.exists():
        raise FileNotFoundError(f"Dossier offres introuvable : {offres_json_dir}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # On prend le dernier fichier brut généré (JSON ou NDJSON).
    json_files = sorted(offres_json_dir.glob("offres_data_market_*.json"))
    ndjson_files = sorted(offres_json_dir.glob("offres_data_market_*.ndjson"))
    all_files = sorted(json_files + ndjson_files)
    if not all_files:
        raise FileNotFoundError(
            f"Aucun fichier 'offres_data_market_*.json/.ndjson' trouvé dans {offres_json_dir}"
        )
    latest_json = all_files[-1]

    print(f"[ft-sqlite] Fichier brut utilisé : {latest_json.name}")

    conn = sqlite3.connect(db_path)
    try:
        # Chargement du JSON brut -> table raw_ft_offres
        load_offres_json_to_raw_table(conn, latest_json, "raw_ft_offres")
    finally:
        conn.close()
    print("[ft-sqlite] Chargement raw terminé. Les transformations doivent être faites via dbt.")
