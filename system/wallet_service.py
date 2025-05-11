# 👛 WalletService (system-level): wraps original service with ConsoleLogger

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from wallets.wallet_service import WalletService as BaseWalletService
from core.logging import log
from wallets.wallet_schema import WalletIn

class WalletService:
    def __init__(self, data_locker):
        self.service = BaseWalletService()
        self.logger = log

    def list_wallets(self):
        try:
            wallets = self.service.list_wallets()
            self.logger.debug(f"Retrieved {len(wallets)} wallet(s).")
            return wallets
        except Exception as e:
            self.logger.error(f"Error listing wallets: {e}")
            raise

    def create_wallet(self, wallet_data: WalletIn):
        try:
            self.service.create_wallet(wallet_data)
            self.logger.success(f"Created wallet '{wallet_data.name}'.")
        except Exception as e:
            self.logger.error(f"Failed to create wallet '{wallet_data.name}': {e}")
            raise

    def delete_wallet(self, name: str):
        try:
            result = self.service.delete_wallet(name)
            if result:
                self.logger.info(f"Deleted wallet '{name}'.")
            else:
                self.logger.warn(f"Wallet '{name}' not found for deletion.")
            return result
        except Exception as e:
            self.logger.error(f"Failed to delete wallet '{name}': {e}")
            raise

    def import_wallets(self):
        try:
            count = self.service.import_wallets_from_json()
            self.logger.info(f"Imported {count} wallet(s) from JSON.")
            return count
        except Exception as e:
            self.logger.error(f"Failed to import wallets: {e}")
            raise

    def export_wallets(self):
        try:
            self.service.export_wallets_to_json()
            self.logger.success("Exported wallets to wallets.json.")
        except Exception as e:
            self.logger.error(f"Failed to export wallets: {e}")
            raise

    def get_wallet(self, name: str):
        try:
            wallet = self.service.get_wallet(name)
            self.logger.debug(f"Fetched wallet '{name}'.")
            return wallet
        except Exception as e:
            self.logger.error(f"Error fetching wallet '{name}': {e}")
            raise

    def update_wallet(self, name: str, data: WalletIn):
        try:
            self.service.update_wallet(name, data)
            self.logger.success(f"Updated wallet '{name}'.")
        except Exception as e:
            self.logger.error(f"Failed to update wallet '{name}': {e}")
            raise
