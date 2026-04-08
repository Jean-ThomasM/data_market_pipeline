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
        print(
            f"[ft-sqlite]   Aucune offre dans {json_path}, table non créée."
        )
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
    print(
        f"[ft-sqlite] Application du SQL de staging depuis {views_sql_path}..."
    )
    conn.executescript(sql)
    conn.commit()
    print("[ft-sqlite] Vues France Travail créées avec succès.")


def main() -> None:
    """
    Charge le dernier fichier JSON d'offres France Travail dans SQLite
    et crée les vues de staging / enrichies.
    """
    db_path = Path("data/geo.sqlite")
    offres_json_dir = Path("data/france_travail_offres")
    offres_views_sql_path = Path("sql/france_travail_offres_views.sql")

    print(f"[ft-sqlite] Base SQLite cible : {db_path.resolve()}")
    print(f"[ft-sqlite] Dossier JSON      : {offres_json_dir.resolve()}")
    print(f"[ft-sqlite] Fichier vues      : {offres_views_sql_path.resolve()}")

    if not offres_json_dir.exists():
        raise FileNotFoundError(f"Dossier JSON introuvable : {offres_json_dir}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # On prend le dernier fichier JSON généré (par ordre alphabétique, qui inclut la date/heure)
    json_files = sorted(offres_json_dir.glob("offres_data_market_*.json"))
    if not json_files:
        raise FileNotFoundError(
            f"Aucun fichier 'offres_data_market_*.json' trouvé dans {offres_json_dir}"
        )
    latest_json = json_files[-1]

    print(f"[ft-sqlite] Fichier JSON utilisé : {latest_json.name}")

    conn = sqlite3.connect(db_path)
    try:
        # Chargement du JSON brut -> table raw_ft_offres
        load_offres_json_to_raw_table(conn, latest_json, "raw_ft_offres")

        # Application du SQL pour créer les vues stg_* et la vue enrichie
        apply_france_travail_views_sql(conn, offres_views_sql_path)
    finally:
        conn.close()
    print(
        "[ft-sqlite] Chargement terminé. Vous pouvez maintenant interroger les vues liées aux offres."
    )


