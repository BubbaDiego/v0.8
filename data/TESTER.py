# initialize_full_schema.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
import os
from core.core_imports import DB_PATH
from core.logging import log

def run_sql(cursor, sql):
    try:
        cursor.execute(sql)
        log.success(f"✅ Executed SQL for table: {sql.split()[2]}", source="SchemaInit")
    except Exception as e:
        log.error(f"❌ Failed to execute SQL: {e}", source="SchemaInit")

def initialize_schema():
    if not os.path.exists(DB_PATH):
        log.error(f"❌ DB path not found: {DB_PATH}", source="SchemaInit")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    log.banner("🛠 Initializing Full DB Schema")

    # Table: positions
    run_sql(cursor, """
        CREATE TABLE IF NOT EXISTS positions (
            id TEXT PRIMARY KEY,
            asset_type TEXT,
            position_type TEXT,
            entry_price REAL,
            current_price REAL,
            liquidation_price REAL,
            collateral REAL,
            size REAL,
            leverage REAL,
            value REAL,
            last_updated TEXT,
            wallet_name TEXT,
            alert_reference_id TEXT,
            hedge_buddy_id TEXT,
            pnl_after_fees_usd REAL,
            travel_percent REAL,
            profit REAL,
            liquidation_distance REAL,
            heat_index REAL,
            current_heat_index REAL,
            status TEXT DEFAULT 'ACTIVE'
        );
    """)

    # Table: alerts
    run_sql(cursor, """
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            alert_type TEXT,
            alert_class TEXT,
            trigger_value REAL,
            notification_type TEXT,
            status TEXT,
            frequency INTEGER,
            counter INTEGER,
            liquidation_distance REAL,
            travel_percent REAL,
            liquidation_price REAL,
            notes TEXT,
            position_reference_id TEXT,
            level TEXT,
            evaluated_value REAL
        );
    """)

    # Table: wallets
    run_sql(cursor, """
        CREATE TABLE IF NOT EXISTS wallets (
            name TEXT PRIMARY KEY,
            public_address TEXT,
            private_address TEXT,
            image_path TEXT,
            balance REAL
        );
    """)

    # Table: brokers
    run_sql(cursor, """
        CREATE TABLE IF NOT EXISTS brokers (
            name TEXT PRIMARY KEY,
            image_path TEXT,
            web_address TEXT,
            total_holding REAL
        );
    """)

    # Table: prices
    run_sql(cursor, """
        CREATE TABLE IF NOT EXISTS prices (
            id TEXT PRIMARY KEY,
            asset_type TEXT,
            current_price REAL,
            previous_price REAL,
            last_update_time TEXT,
            previous_update_time TEXT,
            source TEXT
        );
    """)

    # Table: system_vars
    run_sql(cursor, """
        CREATE TABLE IF NOT EXISTS system_vars (
            id INTEGER PRIMARY KEY DEFAULT 1,
            last_update_time_positions TEXT,
            last_update_positions_source TEXT,
            last_update_time_prices TEXT,
            last_update_prices_source TEXT,
            last_update_time_jupiter TEXT,
            last_update_jupiter_source TEXT,
            total_brokerage_balance REAL,
            total_wallet_balance REAL,
            total_balance REAL,
            strategy_start_value REAL,
            strategy_description TEXT,
            theme_mode TEXT DEFAULT 'light'
        );
    """)

    # Table: positions_totals_history
    run_sql(cursor, """
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
    """)

    conn.commit()
    conn.close()
    log.success("🎉 Full DB schema initialized", source="SchemaInit")


if __name__ == "__main__":
    initialize_schema()
