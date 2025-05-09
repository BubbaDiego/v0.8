


# dl_system_data.py
"""
Author: BubbaDiego
Module: DLSystemDataManager
Description:
    Manages global system data including theme mode, last update timestamps,
    total balances, and strategy performance metadata.

Dependencies:
    - DatabaseManager from database.py
    - ConsoleLogger from console_logger.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.core_imports import log
from data.models import SystemVariables


class DLSystemDataManager:  # 🔥 Renamed from DLSystemVarsManager
    def __init__(self, db):
        self.db = db
        log.info("DLSystemDataManager initialized.", source="DLSystemDataManager")

    def get_theme_mode(self) -> str:
        try:
            cursor = self.db.get_cursor()
            cursor.execute("SELECT theme_mode FROM system_vars WHERE id = 1")
            row = cursor.fetchone()
            theme = row["theme_mode"] if row and row["theme_mode"] else "light"
            log.debug(f"Theme mode retrieved: {theme}", source="DLSystemDataManager")
            return theme
        except Exception as e:
            log.error(f"Error fetching theme mode: {e}", source="DLSystemDataManager")
            return "light"

    def set_theme_mode(self, mode: str):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("UPDATE system_vars SET theme_mode = ? WHERE id = 1", (mode,))
            self.db.commit()
            log.success(f"Theme mode updated to: {mode}", source="DLSystemDataManager")
        except Exception as e:
            log.error(f"Failed to update theme mode: {e}", source="DLSystemDataManager")

    def get_last_update_times(self) -> SystemVariables:
        cursor = self.db.get_cursor()
        cursor.execute("""
            SELECT last_update_time_positions, last_update_positions_source,
                   last_update_time_prices, last_update_prices_source,
                   last_update_time_jupiter, theme_mode,
                   strategy_start_value, strategy_description
            FROM system_vars
            WHERE id = 1
            LIMIT 1
        """)
        row = cursor.fetchone()
        cursor.close()
        if row:
            return SystemVariables(**dict(row))
        else:
            return SystemVariables()

    def set_last_update_times(self, updates: dict):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("""
                UPDATE system_vars SET
                    last_update_time_positions = :last_update_time_positions,
                    last_update_positions_source = :last_update_positions_source,
                    last_update_time_prices = :last_update_time_prices,
                    last_update_prices_source = :last_update_prices_source,
                    last_update_time_jupiter = :last_update_time_jupiter
                WHERE id = 1
            """, updates)
            self.db.commit()
            log.success("System update times saved", source="DLSystemDataManager")
        except Exception as e:
            log.error(f"Error setting system update times: {e}", source="DLSystemDataManager")
