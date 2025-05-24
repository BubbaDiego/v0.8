# data_locker.py
"""
Author: BubbaDiego
Module: DataLocker
Description:
    High-level orchestrator that composes all DL*Manager modules. This is the
    central access point for interacting with alerts, prices, positions, wallets,
    brokers, portfolio data, hedges, and global system state via a unified SQLite backend.

Dependencies:
    - DatabaseManager (SQLite wrapper)
    - DLAlertManager, DLPriceManager, etc.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.database import DatabaseManager
from data.dl_alerts import DLAlertManager
from data.dl_prices import DLPriceManager
from data.dl_positions import DLPositionManager
from data.dl_wallets import DLWalletManager
from data.dl_brokers import DLBrokerManager
from data.dl_portfolio import DLPortfolioManager
from data.dl_system_data import DLSystemDataManager
from data.dl_monitor_ledger import DLMonitorLedgerManager
from data.dl_modifiers import DLModifierManager
from data.dl_hedges import DLHedgeManager
from core.constants import SONIC_SAUCE_PATH

class DataLocker:
    def __init__(self, db_path):
        ...
        self.ledger = DLMonitorLedgerManager(self.db)

from core.core_imports import log
from datetime import datetime


class DataLocker:
    def __init__(self, db_path: str):
        self.db = DatabaseManager(db_path)

        self.alerts = DLAlertManager(self.db)
        self.prices = DLPriceManager(self.db)
        self.positions = DLPositionManager(self.db)
        self.hedges = DLHedgeManager(self.db)
        self.wallets = DLWalletManager(self.db)
        self.brokers = DLBrokerManager(self.db)
        self.portfolio = DLPortfolioManager(self.db)
        self.system = DLSystemDataManager(self.db)
        self.ledger = DLMonitorLedgerManager(self.db)
        self.modifiers = DLModifierManager(self.db)

        self.initialize_database()
        self._seed_modifiers_if_empty()

        log.debug("All DL managers bootstrapped successfully.", source="DataLocker")

    def initialize_database(self):
        """
        Creates all required tables in the database if they do not exist.
        This method can be run safely and repeatedly.
        """
        cursor = self.db.get_cursor()

        table_defs = {
            "wallets": """
                CREATE TABLE IF NOT EXISTS wallets (
                    name TEXT PRIMARY KEY,
                    public_address TEXT,
                    private_address TEXT,
                    image_path TEXT,
                    balance REAL DEFAULT 0.0,
                    tags TEXT DEFAULT '',
                    is_active BOOLEAN DEFAULT 1,
                    type TEXT DEFAULT 'personal'
                )
            """,
            "alerts": """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    alert_type TEXT,
                    alert_class TEXT,
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
                )
            """,
            "alert_thresholds": """
                CREATE TABLE IF NOT EXISTS alert_thresholds (
                    id TEXT PRIMARY KEY,
                    alert_type TEXT NOT NULL,
                    alert_class TEXT NOT NULL,
                    metric_key TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    low REAL NOT NULL,
                    medium REAL NOT NULL,
                    high REAL NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    last_modified TEXT DEFAULT CURRENT_TIMESTAMP,
                    low_notify TEXT,
                    medium_notify TEXT,
                    high_notify TEXT
                )
            """,
            "brokers": """
                CREATE TABLE IF NOT EXISTS brokers (
                    name TEXT PRIMARY KEY,
                    image_path TEXT,
                    web_address TEXT,
                    total_holding REAL DEFAULT 0.0
                )
            """,
            "positions": """
                CREATE TABLE IF NOT EXISTS positions (
                    id TEXT PRIMARY KEY,
                    asset_type TEXT,
                    position_type TEXT,
                    entry_price REAL,
                    liquidation_price REAL,
                    travel_percent REAL,
                    value REAL,
                    collateral REAL,
                    size REAL,
                    leverage REAL,
                    wallet_name TEXT,
                    last_updated TEXT,
                    alert_reference_id TEXT,
                    hedge_buddy_id TEXT,
                    current_price REAL,
                    liquidation_distance REAL,
                    heat_index REAL,
                    current_heat_index REAL,
                    pnl_after_fees_usd REAL
                )
            """,
            "positions_totals_history": """
                CREATE TABLE IF NOT EXISTS positions_totals_history (
                    id TEXT PRIMARY KEY,
                    snapshot_time TEXT,
                    total_size REAL,
                    total_value REAL,
                    total_collateral REAL,
                    avg_leverage REAL,
                    avg_travel_percent REAL,
                    avg_heat_index REAL
                )
            """,
            "modifiers": """
            CREATE TABLE IF NOT EXISTS modifiers (
                key TEXT PRIMARY KEY,
                group_name TEXT NOT NULL,
                value REAL NOT NULL,
                last_modified TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "prices": """
                CREATE TABLE IF NOT EXISTS prices (
                    id TEXT PRIMARY KEY,
                    asset_type TEXT,
                    current_price REAL,
                    previous_price REAL,
                    last_update_time TEXT,
                    previous_update_time TEXT,
                    source TEXT
                )
            """,
            "monitor_heartbeat": """
                CREATE TABLE IF NOT EXISTS monitor_heartbeat (
                    monitor_name TEXT PRIMARY KEY,
                    last_run TIMESTAMP NOT NULL,
                    interval_seconds INTEGER NOT NULL
                )
            """,
            "global_config": """
                CREATE TABLE IF NOT EXISTS global_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """,
            "system_vars": """
            CREATE TABLE IF NOT EXISTS system_vars (
    id TEXT PRIMARY KEY DEFAULT 'main',
    last_update_time_positions TEXT,
    last_update_positions_source TEXT,
    last_update_time_prices TEXT,
    last_update_prices_source TEXT,
    last_update_time_jupiter TEXT,
    last_update_jupiter_source TEXT,  -- ✅ ADD THIS
    theme_mode TEXT,
    theme_active_profile TEXT,        -- ✅ ADD THIS TOO
    strategy_start_value REAL,
    strategy_description TEXT
)
    
        """
        }

        for name, ddl in table_defs.items():
            try:
                cursor.execute(ddl)
                log.debug(f"Table ensured: {name}", source="DataLocker")
            except Exception as e:
                log.error(f"❌ Failed creating table {name}: {e}", source="DataLocker")

        # Ensure a default row exists for system vars so lookups don't fail
        try:
            cursor.execute("INSERT OR IGNORE INTO system_vars (id) VALUES (1)")
        except Exception as e:
            log.error(f"❌ Failed initializing system_vars default row: {e}", source="DataLocker")

        self.db.commit()

    # Inside DataLocker class
    def read_positions(self):
        return self.positions.get_all_positions()

    def set_last_update_times(self, prices_dt, prices_source):
        self.system.set_last_update_times(prices_dt, prices_source)

    def close(self):
        self.db.close()  # Hey
        log.debug("DataLocker shutdown complete.", source="DataLocker")

    def get_latest_price(self, asset_type: str) -> dict:
        return self.prices.get_latest_price(asset_type)

    def set_last_update_times(self, updates: dict):
        self.system.set_last_update_times(updates)

    def get_last_update_times(self) -> dict:
        """Return last update times for positions and prices as a dict."""
        try:
            return self.system.get_last_update_times().to_dict()
        except Exception:
            return {}

    def insert_or_update_price(self, asset_type, price, source="PriceMonitor"):
        from uuid import uuid4
        from datetime import datetime

        price_data = {
            "id": str(uuid4()),
            "asset_type": asset_type,
            "current_price": price,
            "previous_price": 0.0,
            "last_update_time": datetime.now().isoformat(),
            "previous_update_time": None,
            "source": source
        }
        self.prices.insert_price(price_data)

    def get_position_by_reference_id(self, pos_id: str):
        return self.positions.get_position_by_id(pos_id)

    def get_wallet_by_name(self, wallet_name: str):
        return self.wallets.get_wallet_by_name(wallet_name)

    # Wallet convenience wrappers used by repositories
    def read_wallets(self):
        return self.wallets.get_wallets()

    def create_wallet(self, wallet: dict):
        self.wallets.create_wallet(wallet)

    def update_wallet(self, name: str, wallet: dict):
        self.wallets.update_wallet(name, wallet)

    def delete_positions_for_wallet(self, wallet_name: str):
        if hasattr(self.positions, "delete_positions_for_wallet"):
            self.positions.delete_positions_for_wallet(wallet_name)

    # ---- Portfolio convenience wrappers ----
    def get_portfolio_history(self):
        """Return all portfolio snapshot entries."""
        return self.portfolio.get_snapshots()

    def add_portfolio_entry(self, entry: dict):
        """Insert a snapshot entry into the portfolio history."""
        self.portfolio.add_entry(entry)

    def update_portfolio_entry(self, entry_id: str, fields: dict):
        """Update a portfolio history entry by its ID."""
        self.portfolio.update_entry(entry_id, fields)

    def get_portfolio_entry_by_id(self, entry_id: str):
        """Fetch a portfolio history entry by ID."""
        return self.portfolio.get_entry_by_id(entry_id)

    def delete_portfolio_entry(self, entry_id: str):
        """Delete a portfolio history entry."""
        self.portfolio.delete_entry(entry_id)

    def _seed_modifiers_if_empty(self):
        """Seed modifiers table from sonic_sauce.json if empty."""
        cursor = self.db.get_cursor()
        count = cursor.execute("SELECT COUNT(*) FROM modifiers").fetchone()[0]
        if count == 0:
            try:
                with open(SONIC_SAUCE_PATH, "r", encoding="utf-8") as f:
                    data = f.read()
                self.modifiers.import_from_json(data)
                log.debug("Modifiers seeded from sonic_sauce.json", source="DataLocker")
            except Exception as e:
                log.error(f"❌ Failed seeding modifiers: {e}", source="DataLocker")


    def get_all_tables_as_dict(self) -> dict:
        """Return all user tables and their rows as a dictionary."""
        try:
            datasets = {}
            for table in self.db.list_tables():
                datasets[table] = self.db.fetch_all(table)
            return datasets
        except Exception as e:
            log.error(f"❌ Failed to gather tables: {e}", source="DataLocker")
            return {}

