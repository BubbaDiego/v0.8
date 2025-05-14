# monitor/monitors/position_monitor.py

from monitor.base_monitor import BaseMonitor
from data.data_locker import DataLocker
from core.core_imports import DB_PATH
from datetime import datetime, timezone


class PositionMonitor(BaseMonitor):
    """
    Loads all positions and logs summary data.
    """
    def __init__(self):
        super().__init__(name="position_monitor", ledger_filename="position_ledger.json")
        self.dl = DataLocker(str(DB_PATH))

    def _do_work(self):
        positions = self.dl.positions.get_all_positions()
        total = len(positions)
        value_sum = sum(p.get("value", 0.0) for p in positions)
        return {
            "position_count": total,
            "total_value": round(value_sum, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
