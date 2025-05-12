# repair_alerts_sql_and_schema.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
from core.core_imports import DB_PATH
from core.logging import log

REQUIRED_ALERT_COLUMNS = {
    "id": "TEXT PRIMARY KEY",
    "created_at": "TEXT",
    "alert_type": "TEXT",
    "alert_class": "TEXT",
    "asset_type": "TEXT DEFAULT 'ALL'",
    "trigger_value": "REAL",
    "condition": "TEXT DEFAULT 'ABOVE'",
    "notification_type": "TEXT",
    "level": "TEXT DEFAULT 'Normal'",
    "last_triggered": "TEXT",
    "status": "TEXT DEFAULT 'Active'",
    "frequency": "INTEGER DEFAULT 1",
    "counter": "INTEGER DEFAULT 0",
    "liquidation_distance": "REAL DEFAULT 0.0",
    "travel_percent": "REAL DEFAULT 0.0",
    "liquidation_price": "REAL DEFAULT 0.0",
    "notes": "TEXT",
    "description": "TEXT",
    "position_reference_id": "TEXT",
    "evaluated_value": "REAL DEFAULT 0.0",
    "position_type": "TEXT DEFAULT 'N/A'"
}


def repair_alerts_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get current columns
        cursor.execute("PRAGMA table_info(alerts);")
        current_cols = [row[1] for row in cursor.fetchall()]

        # Add any missing columns
        for col_name, col_def in REQUIRED_ALERT_COLUMNS.items():
            if col_name not in current_cols:
                log.info(f"🛠 Adding missing column: {col_name}", source="AlertTableRepair")
                cursor.execute(f"ALTER TABLE alerts ADD COLUMN {col_name} {col_def};")
                conn.commit()
                log.success(f"✅ Added column: {col_name}", source="AlertTableRepair")
            else:
                log.debug(f"✔️ Column exists: {col_name}", source="AlertTableRepair")

        # Check for deprecated columns (like 'asset')
        if "asset" in current_cols:
            log.warning("⚠️ 'asset' column exists but is deprecated — consider migrating data and recreating table without it", source="AlertTableRepair")

        conn.close()
        log.success("🎉 alerts table schema verified and repaired", source="AlertTableRepair")

    except Exception as e:
        log.error(f"❌ Failed to patch alerts table: {e}", source="AlertTableRepair")


if __name__ == "__main__":
    repair_alerts_table()
