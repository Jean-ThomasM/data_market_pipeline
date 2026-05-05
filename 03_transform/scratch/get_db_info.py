import sqlite3

db_path = 'staging_offres_ft.sqlite'
output_path = 'scratch/db_info.txt'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(staging_offres_ft);")
    columns = cursor.fetchall()
    
    with open(output_path, 'w') as f:
        f.write("Columns in staging_offres_ft:\n")
        for col in columns:
            f.write(f" - {col[1]} ({col[2]})\n")
            
    conn.close()
except Exception as e:
    with open(output_path, 'w') as f:
        f.write(f"Error: {e}")
