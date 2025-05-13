import os
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

DB_PATH = os.path.abspath("C:/v0.8/data/mother_brain.db")  # Update if needed

def ensure_table_and_columns(cursor):
    cursor.execute("""
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
            last_modified TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    existing_cols = [row["name"] for row in cursor.execute("PRAGMA table_info(alert_thresholds)")]
    for col in ["low_notify", "medium_notify", "high_notify"]:
        if col not in existing_cols:
            print(f"⚠️  Adding column: {col}")
            cursor.execute(f"ALTER TABLE alert_thresholds ADD COLUMN {col} TEXT")

def notify_str(notify_by):
    mapping = {"call": "Voice", "sms": "SMS", "email": "Email"}
    return ",".join(name for key, name in mapping.items() if notify_by.get(key))

def upsert_threshold(cursor, threshold):
    cursor.execute("""
        SELECT id FROM alert_thresholds
        WHERE alert_type = ? AND alert_class = ?
        LIMIT 1
    """, (threshold["alert_type"], threshold["alert_class"]))
    row = cursor.fetchone()

    if row:
        threshold["id"] = row["id"]
        print(f"📝 Updating: {threshold['alert_type']} ({threshold['alert_class']})")

        cursor.execute("""
            UPDATE alert_thresholds SET
                metric_key = :metric_key,
                condition = :condition,
                low = :low,
                medium = :medium,
                high = :high,
                enabled = :enabled,
                last_modified = :last_modified,
                low_notify = :low_notify,
                medium_notify = :medium_notify,
                high_notify = :high_notify
            WHERE id = :id
        """, threshold)
    else:
        threshold["id"] = str(uuid4())
        print(f"✅ Inserting: {threshold['alert_type']} ({threshold['alert_class']})")
        cursor.execute("""
            INSERT INTO alert_thresholds (
                id, alert_type, alert_class, metric_key, condition,
                low, medium, high, enabled, last_modified,
                low_notify, medium_notify, high_notify
            ) VALUES (
                :id, :alert_type, :alert_class, :metric_key, :condition,
                :low, :medium, :high, :enabled, :last_modified,
                :low_notify, :medium_notify, :high_notify
            )
        """, threshold)

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    ensure_table_and_columns(cursor)

    now = datetime.now(timezone.utc).isoformat()

    definitions = [
        ("Profit", "Position", "profit", {"low": 22, "medium": 51, "high": 99},
         {"low": {"sms": True, "email": True}, "medium": {"email": True}, "high": {"call": True}}),
        ("HeatIndex", "Position", "heat_index", {"low": 7, "medium": 33, "high": 66},
         {"low": {}, "medium": {}, "high": {}}),
        ("TravelPercentLiquid", "Position", "travel_percent_liquid", {"low": -25, "medium": -50, "high": -75},
         {"low": {}, "medium": {}, "high": {}}),
        ("LiquidationDistance", "Position", "liquidation_distance", {"low": 10, "medium": 25, "high": 50},
         {"low": {}, "medium": {}, "high": {}}),
        ("TotalValue", "Portfolio", "total_value", {"low": 10000, "medium": 25000, "high": 50000},
         {"low": {"sms": True}, "medium": {"sms": True, "email": True}, "high": {"sms": True, "email": True, "call": True}}),
        ("TotalSize", "Portfolio", "total_size", {"low": 1, "medium": 5, "high": 10},
         {"low": {}, "medium": {}, "high": {}}),
        ("AvgLeverage", "Portfolio", "avg_leverage", {"low": 1.0, "medium": 5.0, "high": 10.0},
         {"low": {}, "medium": {}, "high": {}}),
        ("AvgTravelPercent", "Portfolio", "avg_travel_percent", {"low": 5, "medium": 15, "high": 30},
         {"low": {}, "medium": {}, "high": {}}),
        ("ValueToCollateralRatio", "Portfolio", "value_to_collateral_ratio", {"low": 0.9, "medium": 1.2, "high": 1.5},
         {"low": {}, "medium": {}, "high": {}}),
        ("TotalHeat", "Portfolio", "total_heat_index", {"low": 10, "medium": 35, "high": 70},
         {"low": {}, "medium": {}, "high": {}}),
        ("PriceThreshold", "Market", "current_price", {"low": 30000, "medium": 40000, "high": 50000},
         {"low": {"sms": True}, "medium": {"sms": True, "email": True}, "high": {"sms": True, "email": True, "call": True}})
    ]

    for alert_type, alert_class, metric_key, ranges, notify_map in definitions:
        threshold = {
            "alert_type": alert_type,
            "alert_class": alert_class,
            "metric_key": metric_key,
            "condition": "ABOVE",
            "low": ranges["low"],
            "medium": ranges["medium"],
            "high": ranges["high"],
            "enabled": True,
            "last_modified": now,
            "low_notify": notify_str(notify_map.get("low", {})),
            "medium_notify": notify_str(notify_map.get("medium", {})),
            "high_notify": notify_str(notify_map.get("high", {}))
        }

        upsert_threshold(cursor, threshold)

    conn.commit()
    conn.close()
    print("✅ Alert thresholds deduplicated and seeded successfully.")

if __name__ == "__main__":
    main()
