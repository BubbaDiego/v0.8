# monitor/monitors/position_monitor.py




from monitor.base_monitor import BaseMonitor
from data.data_locker import DataLocker
from positions.position_core import PositionCore
from core.core_imports import DB_PATH
from datetime import datetime, timezone


class PositionMonitor(BaseMonitor):
    """
    Actively syncs positions from Jupiter and logs summary.
    """
    def __init__(self):
        super().__init__(name="position_monitor", ledger_filename="position_ledger.json")
        self.dl = DataLocker(str(DB_PATH))
        self.core = PositionCore(self.dl)

    def _do_work(self):
        # 🔄 Sync from Jupiter
        sync_result = self.core.update_positions_from_jupiter(source="position_monitor")

        # 🧾 Write to monitor_ledger table
        self.dl.ledger.insert_ledger_entry(
            monitor_name=self.name,
            status="Success" if result["errors"] == 0 else "Error",
            metadata=result
        )

        # 📦 Extract key metrics for ledger
        return {
            "imported": sync_result.get("imported", 0),
            "skipped": sync_result.get("skipped", 0),
            "errors": sync_result.get("errors", 0),
            "hedges": sync_result.get("hedges", 0),
            "timestamp": sync_result.get("timestamp", datetime.now(timezone.utc).isoformat())
        }
