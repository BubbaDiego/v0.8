import sqlite3
import os

# === CONFIG ===
DB_PATH = r"C:\v0.8\data\mother_brain.db"

# === POSITION SCHEMA ===
SCHEMA = """
CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    asset_type TEXT,
    position_type TEXT,
    entry_price REAL,
    liquidation_price REAL,
    collateral REAL,
    size REAL,
    leverage REAL,
    value REAL,
    last_updated TEXT,
    wallet_name TEXT,
    pnl_after_fees_usd REAL,
    travel_percent REAL,
    profit REAL,
    liquidation_distance REAL,
    heat_index REAL,
    current_heat_index REAL,
    alert_reference_id TEXT,
    hedge_buddy_id TEXT,
    current_price REAL -- 🆕 add this to avoid crash
);
"""

def wipe_and_recreate_positions_table(db_path: str):
    if not os.path.exists(db_path):
        print(f"❌ DB file not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        print("💣 Dropping existing 'positions' table...")
        cur.execute("DROP TABLE IF EXISTS positions;")
        conn.commit()

        print("🛠 Rebuilding clean 'positions' table...")
        cur.execute(SCHEMA)
        conn.commit()

        print("✅ Positions table recreated with current_price column.")
    except Exception as e:
        print(f"❌ Failed to reset table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    wipe_and_recreate_positions_table(DB_PATH)
