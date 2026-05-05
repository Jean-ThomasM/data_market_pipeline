import sqlite3

db_path = 'staging_offres_ft.sqlite'
output_path = 'scratch/db_tables.txt'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    with open(output_path, 'w') as f:
        f.write("Tables in database:\n")
        for t in tables:
            f.write(f" - {t[0]}\n")
            # For each table, list columns
            cursor.execute(f"PRAGMA table_info({t[0]});")
            cols = cursor.fetchall()
            for col in cols:
                f.write(f"   * {col[1]} ({col[2]})\n")
            
    conn.close()
except Exception as e:
    with open(output_path, 'w') as f:
        f.write(f"Error: {e}")
