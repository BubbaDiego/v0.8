import os
import sqlite3

# === CONFIG ===
DB_PATH = "mother_brain.db"
TABLE_NAME = "system_vars"
REQUIRED_COLUMNS = {
    "id",
    "last_update_time_positions",
    "last_update_positions_source",
    "last_update_time_prices",
    "last_update_prices_source",
    "last_update_time_jupiter",
    "last_update_jupiter_source",  # ✅ critical one
    "theme_mode",
    "strategy_start_value",
    "strategy_description"
}

def check_db_and_table():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{TABLE_NAME}'
        """)
        result = cursor.fetchone()
        if not result:
            print(f"❌ Table '{TABLE_NAME}' not found in {DB_PATH}")
            return False

        return True

    except Exception as e:
        print(f"❌ DB connection error: {e}")
        return False


def validate_columns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({TABLE_NAME});")
        actual_columns = {row[1] for row in cursor.fetchall()}

        print(f"📋 Found columns in {TABLE_NAME}:\n", actual_columns)

        missing = REQUIRED_COLUMNS - actual_columns
        extra = actual_columns - REQUIRED_COLUMNS

        if missing:
            print(f"❌ MISSING COLUMNS:\n - " + "\n - ".join(missing))
        else:
            print("✅ All required columns are present.")

        if extra:
            print(f"⚠️ Extra columns found (not required):\n - " + "\n - ".join(extra))

    except Exception as e:
        print(f"❌ Failed to inspect columns: {e}")


if __name__ == "__main__":
    print("\n🧠 SCHEMA VALIDATION - mother_brain.db\n" + "="*40)
    if check_db_and_table():
        validate_columns()
    print("="*40)
