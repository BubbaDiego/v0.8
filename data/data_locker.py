# data_locker.py
"""
Author: BubbaDiego
Module: DataLocker
Description:
    High-level orchestrator that composes all DL*Manager modules. This is the
    central access point for interacting with alerts, prices, positions, wallets,
    brokers, portfolio data, and global system state via a unified SQLite backend.

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
from core.core_imports import log

class DataLocker:
    def __init__(self, db_path: str):
        self.db = DatabaseManager(db_path)

        self.alerts = DLAlertManager(self.db)
        self.prices = DLPriceManager(self.db)
        self.positions = DLPositionManager(self.db)
        self.wallets = DLWalletManager(self.db)
        self.brokers = DLBrokerManager(self.db)
        self.portfolio = DLPortfolioManager(self.db)
        self.system = DLSystemDataManager(self.db)

        log.info("All DL managers bootstrapped successfully.", source="DataLocker")

    # Inside DataLocker class
    def read_positions(self):
        return self.positions.get_all_positions()

    def set_last_update_times(self, prices_dt, prices_source):
        self.system.set_last_update_times(prices_dt, prices_source)

    def close(self):
        self.db.close()  # Hey
        log.info("DataLocker shutdown complete.", source="DataLocker")

    def get_latest_price(self, asset_type: str) -> dict:
        return self.prices.get_latest_price(asset_type)

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

