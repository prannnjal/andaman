import sqlite3
import json

# Connect to SQLite
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

data = {}

# Loop through tables and get data
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    # Convert rows to dictionary
    data[table_name] = [dict(zip(columns, row)) for row in rows]

# Write to JSON file
with open('data.json', 'w') as f:
    json.dump(data, f, indent=4)

conn.close()
print("Exported to data.json")
