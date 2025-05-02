import sqlite3
import os
from pathlib import Path

# --- CONFIG ---
BASE_DIR = Path(__file__).resolve().parent.parent  # adjust as needed
DB_PATH = BASE_DIR / "data" / "mother_brain.db"

# --- Expected schema for alerts table ---
ALERTS_COLUMNS = {
    "id": "TEXT PRIMARY KEY",
    "created_at": "DATETIME",
    "alert_type": "TEXT",
    "alert_class": "TEXT",
    "asset": "TEXT",
    "asset_type": "TEXT",
    "trigger_value": "REAL",
    "condition": "TEXT",
    "notification_type": "TEXT",
    "level": "TEXT",
    "last_triggered": "DATETIME",
    "status": "TEXT",
    "frequency": "INTEGER",
    "counter": "INTEGER",
    "liquidation_distance": "REAL",
    "travel_percent": "REAL",
    "liquidation_price": "REAL",
    "notes": "TEXT",
    "description": "TEXT",
    "position_reference_id": "TEXT",
    "evaluated_value": "REAL",
    "position_type": "TEXT"
}

def ensure_alerts_table():
    if not DB_PATH.exists():
        print(f"⚠️ Database not found at {DB_PATH}. Creating new DB file...")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
    exists = cursor.fetchone()

    if not exists:
        print("🚧 Creating 'alerts' table from scratch...")
        columns_sql = ",\n    ".join(f"{col} {type}" for col, type in ALERTS_COLUMNS.items())
        cursor.execute(f"CREATE TABLE alerts (\n    {columns_sql}\n)")
        conn.commit()
        print("✅ 'alerts' table created.")
    else:
        print("ℹ️ 'alerts' table exists. Checking columns...")
        cursor.execute("PRAGMA table_info(alerts)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        for col, col_type in ALERTS_COLUMNS.items():
            if col not in existing_cols:
                print(f"➕ Adding missing column: {col}")
                cursor.execute(f"ALTER TABLE alerts ADD COLUMN {col} {col_type}")
        conn.commit()
        print("✅ Schema check complete. All required columns are present.")

    cursor.close()
    conn.close()
    print("🏁 Done.")

if __name__ == "__main__":
    ensure_alerts_table()
