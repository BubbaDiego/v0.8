import sqlite3
import os
import json

# === CONFIG ===
DB_PATH = "mother_brain.db"  # 🧠 Change this to your actual path

def drop_all(conn):
    cursor = conn.cursor()
    tables = ["alerts", "positions", "wallets"]
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"🧹 Dropped: {table}")
        except Exception as e:
            print(f"⚠️ Failed to drop {table}: {e}")
    conn.commit()

def backup_wallets(conn, backup_path="wallet_backup.json"):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM wallets")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        with open(backup_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Wallets backed up → {backup_path}")
    except Exception as e:
        print(f"❌ Failed to backup wallets: {e}")

def restore_wallets(conn, backup_path="wallet_backup.json"):
    try:
        if not os.path.exists(backup_path):
            print("🚫 Wallet backup not found. Skipping restore.")
            return
        with open(backup_path) as f:
            wallets = json.load(f)

        cursor = conn.cursor()
        for wallet in wallets:
            keys = ", ".join(wallet.keys())
            placeholders = ", ".join("?" for _ in wallet)
            values = tuple(wallet.values())
            cursor.execute(f"INSERT INTO wallets ({keys}) VALUES ({placeholders})", values)
        conn.commit()
        print(f"✅ Wallets restored from {backup_path}")
    except Exception as e:
        print(f"❌ Wallet restore failed: {e}")

def create_schema(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        created_at TEXT,
        alert_type TEXT,
        alert_class TEXT,
        asset TEXT,
        asset_type TEXT,
        trigger_value REAL,
        condition TEXT,
        notification_type TEXT,
        level TEXT,
        last_triggered TEXT,
        status TEXT,
        frequency INTEGER,
        counter INTEGER,
        liquidation_distance REAL,
        travel_percent REAL,
        liquidation_price REAL,
        notes TEXT,
        description TEXT,
        position_reference_id TEXT,
        evaluated_value REAL,
        position_type TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        id TEXT PRIMARY KEY,
        asset_type TEXT,
        entry_price REAL,
        liquidation_price REAL,
        position_type TEXT,
        wallet_name TEXT,
        current_heat_index REAL,
        pnl_after_fees_usd REAL,
        travel_percent REAL,
        liquidation_distance REAL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        id TEXT PRIMARY KEY,
        name TEXT,
        address TEXT,
        network TEXT,
        label TEXT,
        type TEXT
    )""")

    conn.commit()
    print("✅ Perfect schema recreated (alerts, positions, wallets)")

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return

    print(f"🚀 Connecting to DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    backup_wallets(conn)
    drop_all(conn)
    create_schema(conn)
    restore_wallets(conn)

    conn.close()
    print("🎉 DB reset complete.")

if __name__ == "__main__":
    main()
