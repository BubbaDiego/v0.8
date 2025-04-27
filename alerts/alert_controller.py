import json
import logging
import sqlite3
from typing import Optional
from uuid import uuid4
from datetime import datetime

from data.data_locker import DataLocker
from data.models import AlertType, AlertClass, Status
from utils.unified_logger import UnifiedLogger
from utils.update_ledger import log_alert_update
from alerts.alert_enrichment import enrich_alert_data
from config.config_constants import ALERT_LIMITS_PATH


class DummyPositionAlert:
    def __init__(self, alert_type, asset_type, trigger_value, condition, notification_type, position_reference_id, position_type):
        self.id = str(uuid4())
        self.alert_type = alert_type
        self.alert_class = AlertClass.POSITION.value
        self.asset_type = asset_type
        self.trigger_value = trigger_value
        self.condition = condition
        self.notification_type = notification_type
        self.level = "Normal"
        self.last_triggered = None
        self.status = Status.ACTIVE.value
        self.frequency = 1
        self.counter = 0
        self.liquidation_distance = 0.0
        self.travel_percent = 0.0
        self.liquidation_price = 0.0
        self.notes = f"Position {alert_type} alert created"
        self.position_reference_id = position_reference_id
        self.evaluated_value = 0.0
        self.position_type = position_type

    def to_dict(self):
        return self.__dict__


class AlertController:
    def __init__(self, db_path: Optional[str] = None):
        self.u_logger = UnifiedLogger()
        self.logger = logging.getLogger(__name__)
        self.data_locker = DataLocker.get_instance(db_path) if db_path else DataLocker.get_instance()

    def _load_limits(self) -> dict:
        try:
            with open(ALERT_LIMITS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('alert_ranges', {})
        except Exception as e:
            self.logger.error(f"Failed to load alert limits: {e}")
            return {}

    def initialize_alert_data(self, alert_data: dict = None) -> dict:
        defaults = {
            "id": str(uuid4()),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "Normal",
            "status": Status.ACTIVE.value,
            "frequency": 1,
            "counter": 0,
            "liquidation_distance": 0.0,
            "travel_percent": 0.0,
            "liquidation_price": 0.0,
            "notes": "",
            "description": "",
            "last_triggered": None
        }
        alert = alert_data.copy() if alert_data else {}
        for k, v in defaults.items():
            alert.setdefault(k, v)
        return alert

    def create_alert(self, alert_obj) -> bool:
        try:
            alert = alert_obj.to_dict() if not isinstance(alert_obj, dict) else alert_obj
            alert["alert_class"] = (
                AlertClass.MARKET.value if alert["alert_type"] == AlertType.PRICE_THRESHOLD.value
                else AlertClass.POSITION.value
            )
            alert = self.initialize_alert_data(alert)
            cols = ", ".join(alert.keys())
            vals = ", ".join(f":{k}" for k in alert.keys())
            sql = f"INSERT INTO alerts ({cols}) VALUES ({vals})"
            self.data_locker.conn.execute(sql, alert)
            self.data_locker.conn.commit()
            log_alert_update(self.data_locker, alert['id'], 'system', 'Initial creation', '', 'Created')
            return True
        except sqlite3.IntegrityError:
            self.logger.error("IntegrityError creating alert.")
            return False
        except Exception:
            self.logger.exception("Unexpected error in create_alert.")
            return False

    def get_position_type(self, position_id: str) -> str:
        try:
            positions = self.data_locker.read_positions()
            pos = next((p for p in positions if p.get("id") == position_id), None)
            ptype = pos.get("position_type") if pos else None
            return ptype.upper() if ptype and ptype.strip() else "LONG"
        except Exception:
            self.logger.exception("Error retrieving position type; defaulting to LONG.")
            return "LONG"

    def create_alert_for_position(self, pos: dict, alert_type: str, trigger_value: float, condition: str, notification_type: str) -> Optional[dict]:
        alert = DummyPositionAlert(
            alert_type,
            pos.get("asset_type", "BTC"),
            trigger_value,
            condition,
            notification_type,
            pos.get("id"),
            self.get_position_type(pos.get("id"))
        )
        if self.create_alert(alert):
            pos_id = pos.get("id")
            self.data_locker.add_position_alert_mapping(pos_id, alert.alert_type)
            cursor = self.data_locker.conn.cursor()
            cursor.execute("UPDATE positions SET alert_reference_id = ? WHERE id = ?", (alert.id, pos_id))
            self.data_locker.conn.commit()
            return alert.to_dict()
        return None

    # NEW: Cleaner modular creation
    def create_all_position_alerts(self) -> list[dict]:
        created = []
        created += self.create_travel_percent_alerts()
        created += self.create_profit_alerts()
        created += self.create_heat_index_alerts()
        return created

    def create_travel_percent_alerts(self) -> list[dict]:
        created = []
        cfg = self._load_limits().get("travel_percent_liquid_ranges", {})
        if not cfg.get("enabled", False):
            return created

        for pos in self.data_locker.read_positions():
            if not self.data_locker.has_alert_mapping(pos.get("id"), AlertType.TRAVEL_PERCENT_LIQUID.value):
                trigger = float(cfg.get("low", -25.0))
                alert = self.create_alert_for_position(pos, AlertType.TRAVEL_PERCENT_LIQUID.value, trigger, "BELOW", "Call")
                if alert: created.append(alert)
        return created

    def create_profit_alerts(self) -> list[dict]:
        created = []
        cfg = self._load_limits().get("profit_ranges", {})
        if not cfg.get("enabled", False):
            return created

        for pos in self.data_locker.read_positions():
            if not self.data_locker.has_alert_mapping(pos.get("id"), AlertType.PROFIT.value):
                trigger = float(cfg.get("low", 22.0))
                alert = self.create_alert_for_position(pos, AlertType.PROFIT.value, trigger, "ABOVE", "Call")
                if alert: created.append(alert)
        return created

    def create_heat_index_alerts(self) -> list[dict]:
        created = []
        cfg = self._load_limits().get("heat_index_ranges", {})
        if not cfg.get("enabled", False):
            return created

        for pos in self.data_locker.read_positions():
            if not self.data_locker.has_alert_mapping(pos.get("id"), AlertType.HEAT_INDEX.value):
                trigger = float(cfg.get("low", 7.0))
                alert = self.create_alert_for_position(pos, AlertType.HEAT_INDEX.value, trigger, "ABOVE", "Call")
                if alert: created.append(alert)
        return created
