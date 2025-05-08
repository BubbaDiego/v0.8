import sys
import os
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from alerts.alert_utils import (
    normalize_alert_type,
    normalize_condition,
    normalize_notification_type
)

from data.alert import Alert, AlertLevel
#import asyncio
from utils.console_logger import ConsoleLogger as log


class AlertRepository:
    def __init__(self, data_locker):
        self.data_locker = data_locker

    def create_alert(self, alert_obj) -> bool:
        try:
            if not isinstance(alert_obj, dict):
                alert_dict = alert_obj.to_dict()
            else:
                alert_dict = alert_obj

            # Normalize critical fields
            if "alert_type" in alert_dict:
                alert_dict["alert_type"] = normalize_alert_type(alert_dict["alert_type"]).value
            if "condition" in alert_dict:
                alert_dict["condition"] = normalize_condition(alert_dict["condition"]).value
            if "notification_type" in alert_dict:
                alert_dict["notification_type"] = normalize_notification_type(alert_dict["notification_type"]).value

            # 🔧 Safely inject starting_value only if alert is asset-based
            alert_class = alert_dict.get("alert_class", "").lower()
            asset = alert_dict.get("asset")

            if asset and alert_class != "portfolio":
                try:
                    current = self.data_locker.get_current_value(asset)
                    alert_dict["starting_value"] = current
                    log.debug(f"[create_alert] Injected starting_value: {current}", source="AlertRepository")
                except Exception as e:
                    log.warning(f"[create_alert] Could not fetch starting_value for {asset}: {e}",
                                source="AlertRepository")
            else:
                log.debug(f"[create_alert] Skipped starting_value injection for alert_class={alert_class}",
                          source="AlertRepository")

            # 🧱 Initialize default values
            alert_dict = self.data_locker.initialize_alert_data(alert_dict)

            # 📥 DB insert
            cursor = self.data_locker.db.get_cursor()
            sql = """
                INSERT INTO alerts (
                    id,
                    created_at,
                    alert_type,
                    alert_class,
                    asset,
                    asset_type,
                    trigger_value,
                    condition,
                    notification_type,
                    level,
                    last_triggered,
                    status,
                    frequency,
                    counter,
                    liquidation_distance,
                    travel_percent,
                    liquidation_price,
                    notes,
                    description,
                    position_reference_id,
                    evaluated_value,
                    position_type
                ) VALUES (
                    :id, :created_at, :alert_type, :alert_class, :asset, :asset_type,
                    :trigger_value, :condition, :notification_type, :level,
                    :last_triggered, :status, :frequency, :counter, :liquidation_distance,
                    :travel_percent, :liquidation_price, :notes, :description,
                    :position_reference_id, :evaluated_value, :position_type
                )
            """
            cursor.execute(sql, alert_dict)
            self.data_locker.db.commit()
            cursor.close()

            log.success(f"✅ Alert created: {alert_dict['id']}", source="AlertRepository")
            return True

        except sqlite3.IntegrityError as ie:
            log.error(f"❌ IntegrityError creating alert: {ie}", source="AlertRepository")
            return False
        except Exception as ex:
            log.error(f"❌ Unexpected error creating alert: {ex}", source="AlertRepository")
            raise

    def get_active_alerts(self) -> list[Alert]:
        alerts_raw = self.data_locker.get_alerts()

        if not alerts_raw:
            log.warning("No alerts found in database.", source="AlertRepository")
            return []

        log.info(f"Loaded {len(alerts_raw)} alerts from database.", source="AlertRepository")

        alerts = []
        for a in alerts_raw:
            try:
                # 🧼 HARD SANITIZE LEVEL FIELD
                level_raw = a.get("level", "Normal")
                if isinstance(level_raw, str):
                    level_clean = level_raw.strip().capitalize()
                    if level_clean not in {"Normal", "Low", "Medium", "High"}:
                        a["level"] = "Normal"
                    else:
                        a["level"] = level_clean
                else:
                    a["level"] = "Normal"

                # Ensure starting_value exists (fallback for legacy)
                if "starting_value" not in a:
                    a["starting_value"] = a.get("trigger_value", 0)

                alerts.append(Alert(**a))
            except Exception as e:
                log.warning(f"⚠️ Failed to parse alert {a.get('id', '?')} — {str(e)}", source="AlertRepository")

        return alerts

    def update_alert_evaluated_value(self, alert_id: str, evaluated_value: float):
        try:
            cursor = self.data_locker.db.get_cursor()  # ✅ use the injected DataLocker
            sql = """
                UPDATE alerts
                   SET evaluated_value = ?
                 WHERE id = ?
            """
            cursor.execute(sql, (evaluated_value, alert_id))
            self.data_locker.db.commit()
            log.info(f"✅ Updated evaluated_value for alert {alert_id}", source="AlertRepository")
        except Exception as e:
            log.error(f"❌ Failed to update evaluated_value for alert {alert_id}: {e}", source="AlertRepository")

    # ⚠️ NOTE FOR FUTURE GPTs / DEVS:
    # This method is intentionally synchronous.
    # While defined as `def`, it was previously marked `async def` with no real async operations,
    # which caused RuntimeWarnings and broke DB persistence when `await`ed.
    #
    # SQLite in this project uses a synchronous connection via `data_locker.conn`,
    # so DO NOT change this to `async def` unless you're migrating the whole system to a true async DB like aiosqlite.
    #
    # If async support is needed in the future, fully refactor this to use `async with aiosqlite.connect(...)`
    # and propagate awaitables properly.
    #    # Until then: leave as `def` and call it synchronously.

    def update_alert_level(self, alert_id: str, new_level: AlertLevel):
        try:
            # 🧼 Normalize input
            if hasattr(new_level, "value"):
                level_str = new_level.value
            else:
                level_str = str(new_level).capitalize()

            cursor = self.data_locker.db.get_cursor()
            sql = """
                UPDATE alerts
                   SET level = ?
                 WHERE id = ?
            """
            cursor.execute(sql, (level_str, alert_id))
            self.data_locker.db.commit()

            log.info(f"🧪 Updated alert level to '{level_str}' for {alert_id}", source="AlertRepository")

        except Exception as e:
            log.error(f"❌ Failed to update level for alert {alert_id}: {e}", source="AlertRepository")

