import json
import sqlite3
import pandas as pd
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "staging_offres_ft.sqlite"
GEO_DATA_DIR = BASE_DIR.parent / "_old" / "data" / "data_geo"
ADZUNA_NDJSON = BASE_DIR / "offres_adzuna_data_market_20260506_150819.ndjson"

# Mapping Fichier JSON -> Table dbt
MAPPING = {
    "communes.json": "staging_communes",
    "departements.json": "staging_departements",
    "regions.json": "staging_regions",
    "epcis.json": "staging_epcis"
}

def load():
    conn = sqlite3.connect(DB_PATH)
    print(f"Connexion à {DB_PATH}")
    
    # 1. Chargement des données GÉO
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

    # 2. Chargement des données ADZUNA (NDJSON)
    if ADZUNA_NDJSON.exists():
        print(f"Chargement de {ADZUNA_NDJSON} dans staging_offres_adzuna...")
        rows = []
        with open(ADZUNA_NDJSON, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        
        # On utilise json_normalize avec sep='_' pour simuler le schéma BigQuery (ex: company_display_name)
        df_adzuna = pd.json_normalize(rows, sep='_')
        
        # Conversion des listes restantes (ex: location_area) en JSON string pour SQLite
        for col in df_adzuna.columns:
            if df_adzuna[col].apply(lambda x: isinstance(x, list)).any():
                df_adzuna[col] = df_adzuna[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if x is not None else None)

        df_adzuna.to_sql("staging_offres_adzuna", conn, if_exists='replace', index=False)
        print(f"  OK : {len(df_adzuna)} lignes insérées dans staging_offres_adzuna.")
    else:
        print(f"Saut de Adzuna (Fichier {ADZUNA_NDJSON} introuvable)")
    
    conn.close()
    print("Terminé !")

if __name__ == "__main__":
    load()
