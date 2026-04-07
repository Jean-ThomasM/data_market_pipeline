import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Set


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    """
    Charge un fichier JSON qui contient une liste d'objets.
    Aucune transformation n'est appliquée : on renvoie exactement ce qui est dans le JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"Fichier JSON introuvable : {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Le fichier JSON {path} doit contenir une liste d'objets.")
    return data


def _infer_columns(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Détermine l'ensemble des clés présentes dans la liste d'objets JSON
    afin de créer une table qui reflète exactement la structure du JSON.
    """
    cols: Set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            cols.update(row.keys())
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


def load_json_to_raw_table(
    conn: sqlite3.Connection, json_path: Path, table_name: str
) -> None:
    """
    Charge un fichier JSON brut dans une table SQLite "raw_*" avec
    les mêmes colonnes que le JSON (aucune normalisation).
    """
    if not json_path.exists():
        print(f"[geo-sqlite] Fichier JSON introuvable, ignoré : {json_path}")
        return

    print(
        f"[geo-sqlite] Chargement de {json_path} dans la table {table_name} (raw JSON)..."
    )
    rows = _load_json_list(json_path)
    if not rows:
        print(f"[geo-sqlite]   Aucun enregistrement dans {json_path}, table non créée.")
        return

    fieldnames = _infer_columns(rows)
    if not fieldnames:
        print(
            f"[geo-sqlite]   Aucune colonne déduite pour {json_path}, table non créée."
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
            values.append(_serialize_value(row.get(col)))
        to_insert.append(tuple(values))

    if to_insert:
        cur.executemany(
            f'INSERT INTO "{table_name}" ({", ".join(fieldnames)}) VALUES ({placeholders})',
            to_insert,
        )

    conn.commit()
    print(f"[geo-sqlite]   -> {len(to_insert)} lignes insérées dans {table_name}")


def apply_geo_views_sql(conn: sqlite3.Connection, geo_views_sql_path: Path) -> None:
    """
    Exécute le fichier SQL de staging sur la base SQLite (création des vues stg_geo_*).
    """
    if not geo_views_sql_path.exists():
        raise FileNotFoundError(
            f"Fichier SQL de staging introuvable : {geo_views_sql_path}"
        )

    sql = geo_views_sql_path.read_text(encoding="utf-8")
    print(f"[geo-sqlite] Application du SQL de staging depuis {geo_views_sql_path}...")
    conn.executescript(sql)
    conn.commit()
    print("[geo-sqlite] Vues géographiques créées avec succès.")


def main() -> None:
    db_path = Path("data/geo.sqlite")
    geo_json_dir = Path("data/data_geo")
    geo_views_sql_path = Path("sql/geo_views.sql")

    print(f"[geo-sqlite] Base SQLite cible : {db_path.resolve()}")
    print(f"[geo-sqlite] Dossier JSON      : {geo_json_dir.resolve()}")
    print(f"[geo-sqlite] Fichier vues      : {geo_views_sql_path.resolve()}")

    if not geo_json_dir.exists():
        raise FileNotFoundError(f"Dossier JSON introuvable : {geo_json_dir}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        # Chargement des JSON bruts -> tables raw_* miroir exact des JSON
        load_json_to_raw_table(conn, geo_json_dir / "regions.json", "raw_geo_regions")
        load_json_to_raw_table(
            conn, geo_json_dir / "departements.json", "raw_geo_departements"
        )
        load_json_to_raw_table(conn, geo_json_dir / "communes.json", "raw_geo_communes")
        load_json_to_raw_table(conn, geo_json_dir / "epcis.json", "raw_geo_epcis")

        # Application du SQL pour créer les vues geo_*
        apply_geo_views_sql(conn, geo_views_sql_path)
    finally:
        conn.close()
    print(
        "[geo-sqlite] Chargement terminé. Vous pouvez maintenant interroger les vues geo_*."
    )
