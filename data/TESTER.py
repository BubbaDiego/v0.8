import sqlite3
import os
from datetime import datetime

DB_PATH = r"C:\v0.8\data\mother_brain.db"

def ensure_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"🛠️ Connected to DB: {db_path}")

    tables = {
        "positions": """
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                asset_type TEXT,
                position_type TEXT,
                entry_price REAL,
                liquidation_price REAL,
                travel_percent REAL,
                value REAL,
                collateral REAL,
                size REAL,
                leverage REAL,
                wallet_name TEXT,
                last_updated TEXT,
                alert_reference_id TEXT,
                hedge_buddy_id TEXT,
                current_price REAL,
                liquidation_distance REAL,
                heat_index REAL,
                current_heat_index REAL,
                pnl_after_fees_usd REAL,
                profit REAL DEFAULT 0.0,
                status TEXT,
                last_update_jupiter_source TEXT
            );
        """,
        "alerts": """
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                alert_type TEXT,
                alert_class TEXT,
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
            );
        """,
        "alert_thresholds": """
            CREATE TABLE IF NOT EXISTS alert_thresholds (
                id TEXT PRIMARY KEY,
                alert_type TEXT NOT NULL,
                alert_class TEXT NOT NULL,
                metric_key TEXT NOT NULL,
                condition TEXT NOT NULL,
                low REAL NOT NULL,
                medium REAL NOT NULL,
                high REAL NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                last_modified TEXT DEFAULT CURRENT_TIMESTAMP,
                low_notify TEXT,
                medium_notify TEXT,
                high_notify TEXT
            );
        """,
        "wallets": """
            CREATE TABLE IF NOT EXISTS wallets (
                name TEXT PRIMARY KEY,
                public_address TEXT,
                private_address TEXT,
                image_path TEXT,
                balance REAL DEFAULT 0.0,
                tags TEXT DEFAULT '',
                is_active BOOLEAN DEFAULT 1,
                type TEXT DEFAULT 'personal'
            );
        """,
        "prices": """
            CREATE TABLE IF NOT EXISTS prices (
                id TEXT PRIMARY KEY,
                asset_type TEXT,
                current_price REAL,
                previous_price REAL,
                last_update_time TEXT,
                previous_update_time TEXT,
                source TEXT
            );
        """,
        "system_vars": """
            CREATE TABLE IF NOT EXISTS system_vars (
                id TEXT PRIMARY KEY DEFAULT 'main',
                last_update_time_positions TEXT,
                last_update_positions_source TEXT,
                last_update_time_prices TEXT,
                last_update_prices_source TEXT,
                last_update_time_jupiter TEXT,
                last_update_jupiter_source TEXT,
                theme_mode TEXT,
                strategy_start_value REAL,
                strategy_description TEXT
            );
        """,
        "positions_totals_history": """
            CREATE TABLE IF NOT EXISTS positions_totals_history (
                id TEXT PRIMARY KEY,
                snapshot_time TEXT,
                total_size REAL,
                total_value REAL,
                total_collateral REAL,
                avg_leverage REAL,
                avg_travel_percent REAL,
                avg_heat_index REAL
            );
        """
    }

    for name, ddl in tables.items():
        try:
            print(f"🧩 Ensuring table: {name}")
            cursor.execute(ddl)
        except Exception as e:
            print(f"❌ Failed creating {name}: {e}")

    conn.commit()
    conn.close()
    print("✅ All tables ensured.")

if __name__ == "__main__":
    ensure_tables(DB_PATH)
