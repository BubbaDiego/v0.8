import json
import sqlite3

DB_PATH = "mother_brain.db"  # Adjust if needed
JSON_FILE = "com_config.json"
KEY = "xcom_providers"

# Load config
with open(JSON_FILE, "r") as f:
    full_config = json.load(f)

# Isolate the communication.providers block
provider_config = full_config.get("communication", {}).get("providers", {})

if not provider_config:
    print("❌ No providers config found in the JSON")
    exit(1)

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Ensure table exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS global_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
""")

# Insert or update
cursor.execute("""
    INSERT INTO global_config (key, value)
    VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
""", (KEY, json.dumps(provider_config)))

conn.commit()
conn.close()

print("✅ xcom_providers inserted into global_config")
