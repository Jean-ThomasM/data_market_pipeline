import sqlite3

db_path = 'staging_offres_ft.sqlite'
print(f"Inspecting {db_path}...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("PRAGMA table_info(staging_offres_ft);")
    columns = cursor.fetchall()
    print("\nColumns in staging_offres_ft:")
    for col in columns:
        print(f" - {col[1]} ({col[2]})")
        
    # Get a sample row
    cursor.execute("SELECT * FROM staging_offres_ft LIMIT 1;")
    row = cursor.fetchone()
    if row:
        print("\nSample data (first row):")
        names = [description[0] for description in cursor.description]
        for name, value in zip(names, row):
            # Print only first 50 chars of value
            val_str = str(value)[:50] + ("..." if len(str(value)) > 50 else "")
            print(f" {name}: {val_str}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
