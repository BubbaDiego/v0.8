# dl_positions.py
"""
Author: BubbaDiego
Module: DLPositionManager
Description:
    Provides CRUD operations for managing trading positions in the database.
    Supports position creation, listing all positions, and deletion by ID.

Dependencies:
    - DatabaseManager from database.py
    - ConsoleLogger from console_logger.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from uuid import uuid4
from datetime import datetime
from core.core_imports import log

class DLPositionManager:
    def __init__(self, db):
        self.db = db
        log.info("DLPositionManager initialized.", source="DLPositionManager")

    def create_position(self, position: dict):
        try:
            cursor = self.db.get_cursor()

            cursor.execute("""
                INSERT INTO positions (
                    id, asset_type, position_type, entry_price,
                    current_price, liquidation_price, collateral,
                    size, leverage, value, last_updated,
                    wallet_name, alert_reference_id, hedge_buddy_id,
                    pnl_after_fees_usd
                ) VALUES (
                    :id, :asset_type, :position_type, :entry_price,
                    :current_price, :liquidation_price, :collateral,
                    :size, :leverage, :value, :last_updated,
                    :wallet_name, :alert_reference_id, :hedge_buddy_id,
                    :pnl_after_fees_usd
                )
            """, position)

            self.db.commit()

            log.success(f"💾 Position INSERTED: {position['id']}", source="DLPositionManager")
            log.debug(f"📂 DB path in use: {self.db.db_path}", source="DLPositionManager")

        except Exception as e:
            log.error(f"❌ Failed to insert position {position.get('id')}: {e}", source="DLPositionManager")

    def get_all_positions(self) -> list:
        try:
            cursor = self.db.get_cursor()
            cursor.execute("SELECT * FROM positions")
            rows = cursor.fetchall()
            log.debug(f"Fetched {len(rows)} positions", source="DLPositionManager")
            return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"Error fetching positions: {e}", source="DLPositionManager")
            return []


    def delete_position(self, position_id: str):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("DELETE FROM positions WHERE id = ?", (position_id,))
            self.db.commit()
            log.info(f"Deleted position {position_id}", source="DLPositionManager")
        except Exception as e:
            log.error(f"Failed to delete position {position_id}: {e}", source="DLPositionManager")

    def delete_all_positions(self):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("DELETE FROM positions")
            self.db.commit()
            cursor.close()
            log.success("🧹 All positions got fucked", source="DLPositionManager")
        except Exception as e:
            log.error(f"❌ Failed to wipe positions: {e}", source="DLPositionManager")
            raise

    # Primary method
    def delete_positions(self):
        self._delete_all_positions()

    # Alias for dev tools / backcompat
    def clear_positions(self):
        self._delete_all_positions()

    def record_positions_totals_snapshot(self, totals: dict):
        try:
            snapshot_id = str(uuid4())
            snapshot_time = datetime.now().isoformat()
            cursor = self.db.get_cursor()
            cursor.execute("""
                INSERT INTO positions_totals_history (
                    id, snapshot_time, total_size, total_value, total_collateral,
                    avg_leverage, avg_travel_percent, avg_heat_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                snapshot_time,
                totals.get("total_size", 0.0),
                totals.get("total_value", 0.0),
                totals.get("total_collateral", 0.0),
                totals.get("avg_leverage", 0.0),
                totals.get("avg_travel_percent", 0.0),
                totals.get("avg_heat_index", 0.0)
            ))
            self.db.commit()
            log.success(f"📸 Snapshot recorded: {snapshot_id}", source="DataLocker")
        except Exception as e:
            log.error(f"❌ Failed to record position snapshot: {e}", source="DataLocker")
            raise
