import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.core_imports import DB_PATH
import os
import sqlite3
import uuid
import json
from datetime import datetime, timezone
MONITOR_NAME = "test_monitor_console"

# === DB HELPER ===
def ensure_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitor_ledger (
            id TEXT PRIMARY KEY,
            monitor_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def insert_test_entry(conn):
    entry = {
        "id": str(uuid.uuid4()),
        "monitor_name": MONITOR_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "Success",
        "metadata": json.dumps({"test_val": 123, "ok": True})
    }
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO monitor_ledger (
            id, monitor_name, timestamp, status, metadata
        ) VALUES (
            :id, :monitor_name, :timestamp, :status, :metadata
        )
    """, entry)
    conn.commit()
    print("✅ Inserted test ledger entry.")

def read_last_entry(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, status, metadata
        FROM monitor_ledger
        WHERE monitor_name = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (MONITOR_NAME,))
    row = cursor.fetchone()
    if not row:
        print("❌ No entry found.")
        return

    timestamp, status, metadata = row
    print("\n📦 Last Entry")
    print(f"  • Timestamp: {timestamp}")
    print(f"  • Status:    {status}")
    print(f"  • Metadata:  {metadata}")

    # freshness
    try:
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = round((now - ts).total_seconds())
        print(f"  • Age:       {age} seconds ago")
    except Exception as e:
        print(f"❌ Timestamp parse failed: {e}")

if __name__ == "__main__":
    print(f"\n🧠 Testing monitor_ledger in: {DB_PATH}\n")
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found.")
        exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_table(conn)
        insert_test_entry(conn)
        read_last_entry(conn)
    finally:
        conn.close()
