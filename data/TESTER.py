# create_alerts_table.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
import os
from core.core_imports import DB_PATH
from core.logging import log

def create_alerts_table():
    if not os.path.exists(DB_PATH):
        log.error(f"❌ DB not found: {DB_PATH}", source="AlertTableCreator")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Drop old table if needed (WARNING: This will delete existing alerts)
        # Uncomment only if you want a clean start
        # cursor.execute("DROP TABLE IF EXISTS alerts")

        # ✅ Create fresh alerts table — no 'asset' field
        cursor.execute("""
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
            )
        """)

        conn.commit()
        conn.close()
        log.success("✅ 'alerts' table created or verified OK", source="AlertTableCreator")

    except Exception as e:
        log.error(f"❌ Failed to create alerts table: {e}", source="AlertTableCreator")

if __name__ == "__main__":
    create_alerts_table()
