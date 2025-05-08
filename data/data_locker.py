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


from data.database import DatabaseManager
from data.dl_alerts import DLAlertManager
from data.dl_prices import DLPriceManager
from data.dl_positions import DLPositionManager
from data.dl_wallets import DLWalletManager
from data.dl_brokers import DLBrokerManager
from data.dl_portfolio import DLPortfolioManager
from data.dl_system_data import DLSystemDataManager
from utils.console_logger import ConsoleLogger as log

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

        log.banner("DataLocker Initialized ✅")
        log.info("All DL managers bootstrapped successfully.", source="DataLocker")

    # Inside DataLocker class
    def read_positions(self):
        return self.positions.get_all_positions()

    def close(self):
        self.db.close()  # Hey
        log.info("DataLocker shutdown complete.", source="DataLocker")
