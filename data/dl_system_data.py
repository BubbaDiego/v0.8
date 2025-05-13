


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
from datetime import datetime
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
        updates.setdefault("last_update_time_jupiter", datetime.now().isoformat())
        updates.setdefault("last_update_jupiter_source", "sync_engine")

        cursor = self.db.get_cursor()
        cursor.execute("""
            UPDATE system_vars
               SET last_update_time_positions = :last_update_time_positions,
                   last_update_positions_source = :last_update_positions_source,
                   last_update_time_prices = :last_update_time_prices,
                   last_update_prices_source = :last_update_prices_source,
                   last_update_time_jupiter = :last_update_time_jupiter,
                   last_update_jupiter_source = :last_update_jupiter_source
             WHERE id = 1
        """, updates)
        self.db.commit()
        cursor.close()

# ✅ Theme Profile Storage — to be added inside DLSystemDataManager
def get_theme_profiles(self) -> dict:
    try:
        cursor = self.db.get_cursor()
        rows = cursor.execute("SELECT name, config FROM theme_profiles").fetchall()
        return {row["name"]: json.loads(row["config"]) for row in rows}
    except Exception as e:
        log.error(f"Failed to fetch theme profiles: {e}", source="DLSystemDataManager")
        return {}

def insert_or_update_theme_profile(self, name: str, config: dict):
    cursor = self.db.get_cursor()
    cursor.execute("""
        INSERT INTO theme_profiles (name, config)
        VALUES (?, ?)
        ON CONFLICT(name) DO UPDATE SET config = excluded.config
    """, (name, json.dumps(config)))
    self.db.commit()

def delete_theme_profile(self, name: str):
    cursor = self.db.get_cursor()
    cursor.execute("DELETE FROM theme_profiles WHERE name = ?", (name,))
    self.db.commit()

def set_active_theme_profile(self, name: str):
    cursor = self.db.get_cursor()
    cursor.execute("UPDATE system_vars SET theme_active_profile = ? WHERE id = 1", (name,))
    self.db.commit()

def get_active_theme_profile(self) -> dict:
    cursor = self.db.get_cursor()
    row = cursor.execute("SELECT theme_active_profile FROM system_vars WHERE id = 1").fetchone()
    if not row or not row["theme_active_profile"]:
        return {}
    active_name = row["theme_active_profile"]
    all_profiles = self.get_theme_profiles()
    return all_profiles.get(active_name, {})
