# dl_portfolio.py
"""
Author: BubbaDiego
Module: DLPortfolioManager
Description:
    Handles recording and retrieving portfolio snapshots including total size,
    value, collateral, and metrics like leverage and heat index over time.

Dependencies:
    - DatabaseManager from database.py
    - ConsoleLogger from console_logger.py
"""

from utils.console_logger import ConsoleLogger as log
from uuid import uuid4
from datetime import datetime

class DLPortfolioManager:
    def __init__(self, db):
        self.db = db
        log.info("DLPortfolioManager initialized.", source="DLPortfolioManager")

    def record_snapshot(self, totals: dict):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("""
                INSERT INTO positions_totals_history (
                    id, snapshot_time, total_size, total_value,
                    total_collateral, avg_leverage, avg_travel_percent, avg_heat_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid4()),
                datetime.now().isoformat(),
                totals.get("total_size", 0.0),
                totals.get("total_value", 0.0),
                totals.get("total_collateral", 0.0),
                totals.get("avg_leverage", 0.0),
                totals.get("avg_travel_percent", 0.0),
                totals.get("avg_heat_index", 0.0)
            ))
            self.db.commit()
            log.success("Portfolio snapshot recorded", source="DLPortfolioManager")
        except Exception as e:
            log.error(f"Failed to record portfolio snapshot: {e}", source="DLPortfolioManager")

    def get_snapshots(self) -> list:
        try:
            cursor = self.db.get_cursor()
            cursor.execute("SELECT * FROM positions_totals_history ORDER BY snapshot_time ASC")
            rows = cursor.fetchall()
            log.debug(f"Retrieved {len(rows)} portfolio snapshots", source="DLPortfolioManager")
            return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"Failed to fetch portfolio snapshots: {e}", source="DLPortfolioManager")
            return []

    def get_latest_snapshot(self) -> dict:
        try:
            cursor = self.db.get_cursor()
            cursor.execute("SELECT * FROM positions_totals_history ORDER BY snapshot_time DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                log.debug("Latest portfolio snapshot retrieved", source="DLPortfolioManager")
            return dict(row) if row else {}
        except Exception as e:
            log.error(f"Failed to fetch latest snapshot: {e}", source="DLPortfolioManager")
            return {}
