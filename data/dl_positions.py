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
import winsound


class DLPositionManager:
    def __init__(self, db):
        self.db = db
        log.info("DLPositionManager initialized.", source="DLPositionManager")

    def create_position(self, position: dict):
        from datetime import datetime
        import os
        import json
        import traceback

        try:
            # ✅ Ensure required fields are present
            if "current_price" not in position:
                position["current_price"] = 0.0  # Default/fallback
            if "profit" not in position:
                position["profit"] = position.get("value", 0.0)
            if "heat_index" not in position:
                position["heat_index"] = position.get("current_heat_index", 0.0)

            cursor = self.db.get_cursor()

            cursor.execute("""
                INSERT INTO positions (
                    id, asset_type, position_type, entry_price,
                    current_price, liquidation_price, collateral,
                    size, leverage, value, last_updated,
                    wallet_name, alert_reference_id, hedge_buddy_id,
                    pnl_after_fees_usd, travel_percent,
                    profit, liquidation_distance,
                    heat_index, current_heat_index
                ) VALUES (
                    :id, :asset_type, :position_type, :entry_price,
                    :current_price, :liquidation_price, :collateral,
                    :size, :leverage, :value, :last_updated,
                    :wallet_name, :alert_reference_id, :hedge_buddy_id,
                    :pnl_after_fees_usd, :travel_percent,
                    :profit, :liquidation_distance,
                    :heat_index, :current_heat_index
                )
            """, position)

            self.db.commit()

            log.success(f"💾 Position INSERTED: {position['id']}", source="DLPositionManager")
            # 🚨 Play fatal beep on insert error
            winsound.MessageBeep(winsound.MB_ICONHAND)  # Red X system error sound
            winsound.PlaySound("path_to_sound.wav", winsound.SND_FILENAME)

            log.debug(f"📂 DB path in use: {self.db.db_path}", source="DLPositionManager")

        except Exception as e:
            err_msg = f"❌ Failed to insert position {position.get('id')}: {e}"
            log.error(err_msg, source="DLPositionManager")

            tb = traceback.format_exc()
            log.debug(tb, source="DLPositionManager")

            # 🧾 Log failure to file
            try:
                logs_dir = os.path.join(os.path.dirname(self.db.db_path), "..", "logs")
                os.makedirs(logs_dir, exist_ok=True)
                log_path = os.path.join(logs_dir, "dl_failed_inserts.log")

                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n[{datetime.now().isoformat()}] :: INSERT FAIL: {position.get('id')}\n")
                    f.write(f"{err_msg}\n")
                    f.write("Payload:\n")
                    f.write(json.dumps(position, indent=2))
                    f.write("\nTraceback:\n")
                    f.write(tb)
                    f.write("\n" + "=" * 60 + "\n")

                log.warning(f"📄 DL insert error written to: {log_path}", source="DLPositionManager")

            except Exception as file_err:
                log.error(f"⚠️ Failed to write insert failure log: {file_err}", source="DLPositionManager")

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

    def initialize_schema(db):
        cursor = db.get_cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id TEXT PRIMARY KEY,
            asset_type TEXT,
            entry_price REAL,
            liquidation_price REAL,
            position_type TEXT,
            wallet_name TEXT,
            current_heat_index REAL,
            pnl_after_fees_usd REAL,
            travel_percent REAL,
            liquidation_distance REAL
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            alert_type TEXT,
            alert_class TEXT,
            asset TEXT,
            asset_type TEXT,
            trigger_value REAL,
            condition TEXT,
            notification_type TEXT,
            level TEXT,
            last_triggered TEXT,
            status TEXT,
            frequency INTEGER,
            counter INTEGER,
            liquidation_distance REAL,
            travel_percent REAL,
            liquidation_price REAL,
            notes TEXT,
            description TEXT,
            position_reference_id TEXT,
            evaluated_value REAL,
            position_type TEXT
        )""")
        db.commit()

    def insert_position(self, position: dict):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("""
                INSERT INTO positions (
                    id, asset_type, entry_price, liquidation_price,
                    position_type, wallet_name, current_heat_index,
                    pnl_after_fees_usd, travel_percent, liquidation_distance
                ) VALUES (
                    :id, :asset_type, :entry_price, :liquidation_price,
                    :position_type, :wallet_name, :current_heat_index,
                    :pnl_after_fees_usd, :travel_percent, :liquidation_distance
                )
            """, position)
            self.db.commit()
            log.success(f"✅ Position inserted for test: {position['id']}", source="DLPositionManager")
        except Exception as e:
            log.error(f"❌ Failed to insert test position: {e}", source="DLPositionManager")

    def get_position_by_id(self, pos_id: str):
        cursor = self.db.get_cursor()
        cursor.execute("SELECT * FROM positions WHERE id = ?", (pos_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
