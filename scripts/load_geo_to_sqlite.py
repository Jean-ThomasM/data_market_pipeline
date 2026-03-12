import argparse
import csv
import sqlite3
from pathlib import Path


def load_csv_to_table(conn: sqlite3.Connection, csv_path: Path, table_name: str) -> None:
    """
    Charge un fichier CSV dans une table SQLite "brute" (raw_*).
    Toutes les colonnes sont créées en TEXT pour garder la flexibilité ;
    la couche de staging se chargera du typage fin (cast, etc.).
    """
    if not csv_path.exists():
        print(f"[geo-sqlite] Fichier CSV introuvable, ignoré : {csv_path}")
        return

    print(f"[geo-sqlite] Chargement de {csv_path} dans la table {table_name}...")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print(f"[geo-sqlite]   Aucun champ trouvé dans {csv_path}, table non créée.")
            return

        cols_def = ", ".join(f'"{name}" TEXT' for name in fieldnames)

        cur = conn.cursor()
        cur.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        cur.execute(f'CREATE TABLE "{table_name}" ({cols_def})')

        placeholders = ", ".join(["?"] * len(fieldnames))
        rows = [tuple(row.get(col, "") for col in fieldnames) for row in reader]

        if rows:
            cur.executemany(
                f'INSERT INTO "{table_name}" ({", ".join(fieldnames)}) VALUES ({placeholders})',
                rows,
            )

        conn.commit()
        print(f"[geo-sqlite]   -> {len(rows)} lignes insérées dans {table_name}")


def apply_staging_sql(conn: sqlite3.Connection, staging_sql_path: Path) -> None:
    """
    Exécute le fichier SQL de staging sur la base SQLite (création des vues stg_geo_*).
    """
    if not staging_sql_path.exists():
        raise FileNotFoundError(f"Fichier SQL de staging introuvable : {staging_sql_path}")

    sql = staging_sql_path.read_text(encoding="utf-8")
    print(f"[geo-sqlite] Application du SQL de staging depuis {staging_sql_path}...")
    conn.executescript(sql)
    conn.commit()
    print("[geo-sqlite] Vues de staging créées avec succès.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Charge les CSV géographiques dans une base SQLite et crée les vues de staging."
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/geo.sqlite",
        help="Chemin du fichier SQLite à créer/utiliser (par défaut: data/geo.sqlite).",
    )
    parser.add_argument(
        "--csv-dir",
        type=str,
        default="data/processed_geo",
        help="Dossier contenant les CSV géographiques (par défaut: data/processed_geo).",
    )
    parser.add_argument(
        "--staging-sql",
        type=str,
        default="sql/staging_geo.sql",
        help="Chemin du fichier SQL de staging (par défaut: sql/staging_geo.sql).",
    )

    args = parser.parse_args()

    db_path = Path(args.db_path)
    csv_dir = Path(args.csv_dir)
    staging_sql_path = Path(args.staging_sql)

    print(f"[geo-sqlite] Base SQLite cible : {db_path.resolve()}")
    print(f"[geo-sqlite] Dossier CSV       : {csv_dir.resolve()}")
    print(f"[geo-sqlite] Fichier staging   : {staging_sql_path.resolve()}")

    if not csv_dir.exists():
        raise FileNotFoundError(f"Dossier CSV introuvable : {csv_dir}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        # Chargement des tables brutes (bronze) à partir des CSV
        load_csv_to_table(conn, csv_dir / "regions.csv", "raw_geo_regions")
        load_csv_to_table(conn, csv_dir / "departements.csv", "raw_geo_departements")
        load_csv_to_table(conn, csv_dir / "communes.csv", "raw_geo_communes")
        load_csv_to_table(
            conn,
            csv_dir / "communes_codes_postaux.csv",
            "raw_geo_communes_codes_postaux",
        )
        load_csv_to_table(conn, csv_dir / "epcis.csv", "raw_geo_epcis")

        # Application du SQL de staging pour créer les vues stg_geo_*
        apply_staging_sql(conn, staging_sql_path)

        print("[geo-sqlite] Chargement terminé. Vous pouvez maintenant interroger les vues stg_geo_*.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

