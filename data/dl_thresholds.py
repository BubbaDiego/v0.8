# dl_thresholds.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.core_imports import log
from datetime import datetime, timezone
from data.models import AlertThreshold
from uuid import uuid4
from datetime import datetime

class DLThresholdManager:
    def __init__(self, db):
        self.db = db
        log.debug("DLThresholdManager initialized.", source="DLThresholdManager")

    def get_all(self) -> list:
        cursor = self.db.get_cursor()
        rows = cursor.execute("SELECT * FROM alert_thresholds ORDER BY alert_type").fetchall()
        return [AlertThreshold(**dict(row)) for row in rows]

    def get_by_type_and_class(self, alert_type: str, alert_class: str, condition: str) -> AlertThreshold:
        cursor = self.db.get_cursor()
        row = cursor.execute("""
            SELECT * FROM alert_thresholds
            WHERE alert_type = ? AND alert_class = ? AND condition = ? AND enabled = 1
            ORDER BY last_modified DESC LIMIT 1
        """, (alert_type, alert_class, condition)).fetchone()
        return AlertThreshold(**dict(row)) if row else None

    def insert(self, threshold: AlertThreshold) -> bool:
        try:
            cursor = self.db.get_cursor()
            cursor.execute("""
                INSERT INTO alert_thresholds (
                    id, alert_type, alert_class, metric_key,
                    condition, low, medium, high, enabled, last_modified
                ) VALUES (
                    :id, :alert_type, :alert_class, :metric_key,
                    :condition, :low, :medium, :high, :enabled, :last_modified
                )
            """, threshold.to_dict())
            self.db.commit()
            return True
        except Exception as e:
            log.error(f"❌ Failed to insert threshold: {e}", source="DLThresholdManager")
            return False

    def update(self, threshold_id: str, fields: dict):
        try:
            # Sanitize: convert list fields to comma strings
            for k in ['low_notify', 'medium_notify', 'high_notify']:
                if k in fields and isinstance(fields[k], list):
                    fields[k] = ",".join(fields[k])

            # Set last_modified
            fields["last_modified"] = datetime.now(timezone.utc).isoformat()
            fields["id"] = threshold_id

            # Generate SQL SET clause dynamically
            updates = ", ".join(f"{key} = :{key}" for key in fields if key != "id")
            cursor = self.db.get_cursor()
            cursor.execute(f"""
                UPDATE alert_thresholds SET {updates} WHERE id = :id
            """, fields)
            self.db.commit()
            log.success(f"✅ Threshold {threshold_id} updated", source="DLThresholdManager")
            return True

        except Exception as e:
            log.error(f"❌ Failed to update threshold {threshold_id}: {e}", source="DLThresholdManager")
            return False

    def delete(self, threshold_id: str):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("DELETE FROM alert_thresholds WHERE id = ?", (threshold_id,))
            self.db.commit()
            return True
        except Exception as e:
            log.error(f"❌ Failed to delete threshold {threshold_id}: {e}", source="DLThresholdManager")
            return False
