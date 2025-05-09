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

    def clear_positions(self):
        print("🔥 DLPositionManager.clear_positions CALLED")

        try:
            cursor = self.db.get_cursor()
            cursor.execute("DELETE FROM positions")
            self.db.commit()
            log.warning("🧹 All positions cleared from DB.", source="DLPositionManager")
        except Exception as e:
            log.error(f"❌ Failed to clear positions: {e}", source="DLPositionManager")
