import json
import sqlite3
import pandas as pd
from pathlib import Path

# Chemins
DB_PATH = Path("staging_offres_ft.sqlite")
GEO_DATA_DIR = Path("../_old/data/data_geo")

# Mapping Fichier JSON -> Table dbt
MAPPING = {
    "communes.json": "staging_communes",
    "departements.json": "staging_departements",
    "regions.json": "staging_regions",
    "epcis.json": "staging_epcis"
}

def load():
    if not DB_PATH.exists():
        print(f"Erreur : La base {DB_PATH} n'existe pas dans {Path.cwd()}")
        return

    conn = sqlite3.connect(DB_PATH)
    print(f"Connexion à {DB_PATH}")
    
    for json_file, table_name in MAPPING.items():
        path = GEO_DATA_DIR / json_file
        if not path.exists():
            print(f"Saut de {json_file} (introuvable dans {GEO_DATA_DIR})")
            continue
            
        print(f"Chargement de {json_file} dans {table_name}...")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        df = pd.DataFrame(data)
        # On convertit les listes/dicts en chaînes JSON pour SQLite
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if x is not None else None)
        
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"  OK : {len(df)} lignes insérées.")
    
    conn.close()
    print("Terminé !")

if __name__ == "__main__":
    load()
