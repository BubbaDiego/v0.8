# alerts/alert_store.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from alert_core.alert_utils import normalize_alert_type, normalize_condition, normalize_notification_type
from data.alert import AlertType, Condition
from data.models import AlertClass

from data.models import (
    AlertType,
    AlertClass,
    NotificationType,
    Status
)


from alert_core.alert_utils import log_alert_summary
from uuid import uuid4
from core.logging import log
from datetime import datetime
from data.alert import Alert, AlertLevel
import sqlite3

PORTFOLIO_POSITION_ID = "619"

# 🔐 Enum Sanity Check
from data.models import AlertType

REQUIRED_ALERT_TYPES = [
    "TOTAL_VALUE",
    "TOTAL_SIZE",
    "TOTAL_LEVERAGE",
    "TOTAL_RATIO",
    "TOTAL_TRAVEL_PERCENT",
    "TOTAL_HEAT_INDEX"
]

for enum_name in REQUIRED_ALERT_TYPES:
    assert hasattr(AlertType, enum_name), f"❌ Missing AlertType.{enum_name} — restart required or model desynced"


class AlertStore:
    def __init__(self, data_locker, config_loader=None):
        """Persist alerts to the database.

        Parameters
        ----------
        data_locker : DataLocker
            Wrapper around the database access layer.
        config_loader : callable, optional
            Function returning the alert configuration dictionary.  When None,
            a stub loader that returns an empty dict is used.
        """

        self.data_locker = data_locker
        if config_loader:
            self.config_loader = config_loader
        else:
            self.config_loader = (
                lambda: self.data_locker.system.get_var("alert_limits") or {}
            )

    @staticmethod
    def initialize_alert_data(alert_data: dict = None) -> dict:
        from data.models import Status, AlertLevel
        from uuid import uuid4
        from datetime import datetime

        defaults = {
            "id": str(uuid4()),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "alert_type": "",
            "alert_class": "",
            "asset_type": "BTC",
            "trigger_value": 0.0,
            "condition": "ABOVE",
            "notification_type": "Email",
            "level": AlertLevel.NORMAL.value,
            "last_triggered": None,
            "status": Status.ACTIVE.value,
            "frequency": 1,
            "counter": 0,
            "liquidation_distance": 0.0,
            "travel_percent": 0.0,
            "liquidation_price": 0.0,
            "notes": "",
            "description": "",
            "position_reference_id": None,
            "evaluated_value": 0.0,
            "position_type": "N/A"#,
        #    "asset": "PORTFOLIO"
        }

        alert_data = alert_data or {}

        for key, default_val in defaults.items():
            if key not in alert_data or alert_data.get(key) is None:
                alert_data[key] = default_val
            elif key == "position_reference_id":
                value = alert_data.get(key)
                if isinstance(value, str) and value.strip() == "":
                    from core.core_imports import log
                    log.error("⚠️ Empty position_reference_id in alert", source="AlertStore")

        return alert_data

    def create_alert(self, alert_obj) -> bool:
        try:
            if not isinstance(alert_obj, dict):
                alert_dict = alert_obj.to_dict()
            else:
                alert_dict = alert_obj

            # Normalize enums
            if "alert_type" in alert_dict:
                alert_dict["alert_type"] = normalize_alert_type(alert_dict["alert_type"]).value
            if "condition" in alert_dict:
                alert_dict["condition"] = normalize_condition(alert_dict["condition"]).value
            if "notification_type" in alert_dict:
                alert_dict["notification_type"] = normalize_notification_type(alert_dict["notification_type"]).value

            # Finalize defaults
            alert_dict = self.initialize_alert_data(alert_dict)

            # Insert — only 21 fields, asset removed
            cursor = self.data_locker.db.get_cursor()
            sql = """
                INSERT INTO alerts (
                    id, created_at, alert_type, alert_class, asset_type,
                    trigger_value, condition, notification_type, level,
                    last_triggered, status, frequency, counter, liquidation_distance,
                    travel_percent, liquidation_price, notes, description,
                    position_reference_id, evaluated_value, position_type
                ) VALUES (
                    :id, :created_at, :alert_type, :alert_class, :asset_type,
                    :trigger_value, :condition, :notification_type, :level,
                    :last_triggered, :status, :frequency, :counter, :liquidation_distance,
                    :travel_percent, :liquidation_price, :notes, :description,
                    :position_reference_id, :evaluated_value, :position_type
                )
            """
            cursor.execute(sql, alert_dict)
            self.data_locker.db.commit()
            cursor.close()

            log.success(f"✅ Alert created: {alert_dict['id']}", source="AlertStore")
            return True

        except sqlite3.IntegrityError as ie:
            log.error(f"❌ Integrity error: {ie}", source="AlertStore")
            return False
        except Exception as e:
            log.error(f"❌ Failed to create alert", source="AlertStore", payload={"error": str(e)})
            raise

    def delete_alert(self, alert_id: str) -> bool:
        try:
            cursor = self.data_locker.db.get_cursor()
            cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
            self.data_locker.db.commit()
            log.info(f"🗑 Deleted alert {alert_id}", source="AlertStore")
            return True
        except Exception as e:
            log.error(f"❌ Failed to delete alert {alert_id}: {e}", source="AlertStore")
            return False

    def get_alerts(self) -> list:
        try:
            cursor = self.data_locker.db.get_cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"❌ Failed to fetch alerts", source="AlertStore", payload={"error": str(e)})
            return []

    def get_all_alerts(self) -> list:
        return self.get_alerts()

    def get_active_alerts(self) -> list[Alert]:
        alerts_raw = self.get_alerts()

        if not alerts_raw:
            log.warning("⚠️ No alerts found in DB", source="AlertStore")
            return []

        active_alerts = []
        for a in alerts_raw:
            try:
                if a.get("status") != "Active":
                    continue

                level = a.get("level", "Normal").strip().capitalize()
                if level not in {"Normal", "Low", "Medium", "High"}:
                    a["level"] = "Normal"
                else:
                    a["level"] = level

                if "starting_value" not in a:
                    a["starting_value"] = a.get("trigger_value", 0)

                active_alerts.append(Alert(**a))  # ✅ convert dict → Alert model
            except Exception as e:
                log.warning(f"⚠️ Failed to parse alert {a.get('id', '?')} — {e}", source="AlertStore")

        log.info(f"✅ Loaded {len(active_alerts)} active alerts", source="AlertStore")
        return active_alerts

    def create_position_alerts(self):
        log.banner("📊 AlertStore: Creating Position Alerts")
        positions = self.data_locker.positions.get_all_positions()
        created = 0

        config = self.config_loader() or {}
        pos_cfg = config.get("alert_ranges", {}).get("positions_alerts", {})

        for pos in positions:
            pos_id = pos.get("id")
            pos_type = pos.get("position_type", "N/A")
            asset_type = pos.get("asset_type", "OTHER")

            try:
                alerts = [
                    {
                        "alert_type": AlertType.HEAT_INDEX.value,
                        "description": "heat_index",
                        "trigger_value": 30.0,
                    },
                    {
                        "alert_type": AlertType.TRAVEL_PERCENT_LIQUID.value,
                        "description": "travel_percent",
                        "trigger_value": 100.0,
                    },
                    {
                        "alert_type": AlertType.PROFIT.value,
                        "description": "profit",
                        "trigger_value": 50.0,
                    },
                ]

                for spec in alerts:
                    metric_cfg = pos_cfg.get(spec["description"])
                    # Skip alert creation if explicitly disabled or key is missing
                    if not metric_cfg or not metric_cfg.get("enabled", False):
                        continue

                    trig_val = metric_cfg.get("medium", spec["trigger_value"])

                    alert = {
                        "id": str(uuid4()),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "alert_type": spec["alert_type"],
                        "alert_class": AlertClass.POSITION.value,
                        "asset_type": asset_type,
                        "trigger_value": trig_val,
                        "condition": Condition.ABOVE.value,
                        "notification_type": NotificationType.SMS.value,
                        "level": "Normal",
                        "last_triggered": None,
                        "status": Status.ACTIVE.value,
                        "frequency": 1,
                        "counter": 0,
                        "liquidation_distance": pos.get("liquidation_distance", 0.0),
                        "travel_percent": pos.get("travel_percent", 0.0),
                        "liquidation_price": pos.get("liquidation_price", 0.0),
                        "notes": f"Auto-generated alert for {spec['description']}",
                        "description": spec["description"],
                        "position_reference_id": pos_id,
                        "evaluated_value": 0.0,
                        "position_type": pos_type
                    }

                    self.create_alert(alert)
                    log_alert_summary(alert)
                    created += 1

            except Exception as e:
                log.error(f"❌ Skipped alert for position {pos_id}: {e}", source="AlertStore")

        log.success(f"✅ Position alert creation complete: {created} alerts", source="AlertStore")



    def create_portfolio_alerts(self):
        log.banner("📦 AlertStore: Creating Portfolio Alerts")
        created = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        config = self.config_loader() or {}
        port_cfg = config.get("alert_ranges", {}).get("portfolio_alerts", {})

        metrics = [
            (AlertType.TOTAL_VALUE, "total_value", 50000, Condition.ABOVE),
            (AlertType.TOTAL_SIZE, "total_size", 1.0, Condition.ABOVE),
            (AlertType.TOTAL_LEVERAGE, "avg_leverage", 2.0, Condition.ABOVE),
            (AlertType.TOTAL_TRAVEL_PERCENT, "avg_travel_percent", 10.0, Condition.ABOVE),
            (AlertType.TOTAL_RATIO, "value_to_collateral_ratio", 1.2, Condition.BELOW),
            (AlertType.TOTAL_HEAT_INDEX, "total_heat", 25.0, Condition.ABOVE),
        ]

        for alert_type, description, trigger_value, condition in metrics:
            metric_cfg = port_cfg.get(description)
            # Skip when disabled or missing in config
            if not metric_cfg or not metric_cfg.get("enabled", False):
                continue

            trig_val = metric_cfg.get("medium", trigger_value)

            try:
                alert = {
                    "id": str(uuid4()),
                    "created_at": now,
                    "alert_type": alert_type.value,  # ✅ enum.value is already lowercase
                    "alert_class": AlertClass.PORTFOLIO.value,
                    "asset_type": "ALL",
                    "trigger_value": trig_val,
                    "condition": condition.value,
                    "notification_type": NotificationType.SMS.value,
                    "level": "Normal",
                    "last_triggered": None,
                    "status": Status.ACTIVE.value,
                    "frequency": 1,
                    "counter": 0,
                    "liquidation_distance": 0.0,
                    "travel_percent": 0.0,
                    "liquidation_price": 0.0,
                    "notes": f"Auto-generated portfolio alert for {description}",
                    "description": description,
                    "position_reference_id": PORTFOLIO_POSITION_ID,
                    "evaluated_value": 0.0,
                    "position_type": "N/A"
                }

                self.create_alert(alert)
                log_alert_summary(alert)
                created += 1

            except Exception as e:
                log.error(f"💥 Failed to create alert for {description}: {e}", source="AlertStore")

        log.success(f"✅ Portfolio alert creation complete: {created} alerts", source="AlertStore")

    def create_global_alerts(self):
        log.banner("🌐 AlertStore: Creating Global Market Alerts")
        try:
            alert = {
                "id": str(uuid4()),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "alert_type": AlertType.PriceThreshold.value,
                "alert_class": "Market",
                "asset": "BTC",
                "asset_type": "Crypto",
                "trigger_value": 65000,
                "condition": Condition.ABOVE.value,
                "notification_type": "SMS",
                "level": "Normal",
                "last_triggered": None,
                "status": "Active",
                "frequency": 1,
                "counter": 0,
                "liquidation_distance": 0.0,
                "travel_percent": 0.0,
                "liquidation_price": 0.0,
                "notes": "BTC price alert",
                "description": "BTC threshold",
                "position_reference_id": None,
                "evaluated_value": 0.0,
                "position_type": "N/A"
            }

            self.create_alert(alert)
            log.success("✅ Global BTC price alert created", source="AlertStore")

        except Exception as e:
            log.error(f"💥 Failed to create global alert: {e}", source="AlertStore")


