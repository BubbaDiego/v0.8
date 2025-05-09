import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
from datetime import datetime
from uuid import uuid4
from monitor.price_monitor import PriceMonitor
from alerts.alert_service_manager import AlertServiceManager
from core.logging import log
from core.constants import DB_PATH, ALERT_LIMITS_PATH
from config.config_loader import load_config

from cyclone.cyclone_position_service import CyclonePositionService
from cyclone.cyclone_portfolio_service import CyclonePortfolioService
from cyclone.cyclone_alert_service import CycloneAlertService
from cyclone.cyclone_hedge_service import CycloneHedgeService


from data.data_locker import DataLocker
from core.constants import DB_PATH

global_data_locker = DataLocker(str(DB_PATH))  # SINGLE SOURCE OF TRUTH


def configure_cyclone_console_log():
    """
    🧠 Centralized Cyclone Console Log Config
    Enables all core modules for debugging.
    """
    log.silence_module("werkzeug")
    log.silence_module("fuzzy_wuzzy")

    log.assign_group("cyclone_core", [
        # Core engine & service modules
        "cyclone_engine", "Cyclone",
        "CycloneHedgeService", "CyclonePortfolioService",
        "CycloneAlertService", "CyclonePositionService",

        # Deep services
        "PositionSyncService", "PositionCoreService", "PositionEnrichmentService",
        "AlertEvaluator", "AlertController", "AlertServiceManager",

        # Data & Utility modules
        "DataLocker", "PriceMonitor", "DBCore", "Logger", "AlertUtils",
        "CalcServices", "LockerFactory",

        # Experimental or custom
        "HedgeManager", "CycleRunner", "ConsoleHelper"
    ])

    log.enable_group("cyclone_core")
    log.init_status()


class Cyclone:
    def __init__(self, poll_interval=60):
        self.logger = logging.getLogger("Cyclone")
        self.poll_interval = poll_interval
        self.logger.setLevel(logging.DEBUG)

        log.info("Initializing Cyclone engine...", source="Cyclone")

        self.data_locker = global_data_locker

       # self.data_locker = DataLocker(str(DB_PATH))
        self.price_monitor = PriceMonitor()
        self.alert_service = AlertServiceManager.get_instance()
        self.config = load_config(str(ALERT_LIMITS_PATH))

        self.portfolio_runner = CyclonePortfolioService(self.data_locker)
        self.position_runner = CyclonePositionService(self.data_locker)
        self.alert_runner = CycloneAlertService(self.data_locker)
        self.hedge_runner = CycloneHedgeService(self.data_locker)

        log.banner("🌀  🌪️ CYCLONE ENGINE STARTUP 🌪️ 🌀")
        log.success("Cyclone orchestrator initialized.", source="Cyclone")

    async def run_market_updates(self):
        log.info("Starting Market Updates", source="Cyclone")
        try:
            await self.price_monitor.update_prices(source="Market Updates")
            log.success("Prices updated successfully", source="Cyclone")
        except Exception as e:
            log.error(f"Market Updates failed: {e}", source="Cyclone")

    async def run_composite_position_pipeline(self):
        await asyncio.to_thread(self.position_runner.update_positions_from_jupiter)

    def clear_prices_backend(self):
        try:
            cursor = self.data_locker.db.get_cursor()
            cursor.execute("DELETE FROM prices")
            self.data_locker.db.commit()
            deleted = cursor.rowcount
            cursor.close()
            print(f"🧹 Prices cleared. {deleted} record(s) deleted.")
        except Exception as e:
            print(f"❌ Error clearing prices: {e}")

    def clear_wallets_backend(self):
        try:
            cursor = self.data_locker.db.get_cursor()
            cursor.execute("DELETE FROM wallets")
            self.data_locker.db.commit()
            deleted = cursor.rowcount
            cursor.close()
            print(f"🧹 Wallets cleared. {deleted} record(s) deleted.")
        except Exception as e:
            print(f"Error clearing wallets: {e}")

    def add_wallet_backend(self):
        try:
            name = input("Enter wallet name: ").strip()
            public_address = input("Enter public address: ").strip()
            private_address = input("Enter private address: ").strip()
            image_path = input("Enter image path (optional): ").strip()
            balance_str = input("Enter balance (optional): ").strip()
            try:
                balance = float(balance_str)
            except Exception:
                balance = 0.0

            wallet = {
                "name": name,
                "public_address": public_address,
                "private_address": private_address,
                "image_path": image_path,
                "balance": balance
            }

            self.data_locker.wallets.create_wallet(wallet)
            print(f"✅ Wallet '{name}' added successfully.")
        except Exception as e:
            print(f"Error adding wallet: {e}")

    def view_wallets_backend(self):
        try:
            wallets = self.data_locker.wallets.get_wallets()
            if not wallets:
                print("⚠️ No wallets found.")
                return

            print("💼 Wallets")
            print(f"📦 Total: {len(wallets)}\n")
            for w in wallets:
                print(f"🧾 Name:     {w['name']}")
                print(f"🏦 Address:  {w['public_address']}")
                print(f"💰 Balance:  {w['balance']}")
                print(f"🖼️ Image:    {w['image_path']}")
                print("-" * 40)
        except Exception as e:
            print(f"❌ Error viewing wallets: {e}")

    async def run_create_market_alerts(self):
        log.info("Creating Market Alerts", source="Cyclone")
        try:
            dummy_alert = {
                "id": str(uuid4()),
                "alert_type": "PRICE_THRESHOLD",
                "alert_class": "Market",
                "asset_type": "BTC",
                "trigger_value": 60000,
                "condition": "ABOVE",
                "notification_type": "SMS",
                "level": "Normal",
                "last_triggered": None,
                "status": "Active",
                "frequency": 1,
                "counter": 0,
                "liquidation_distance": 0.0,
                "travel_percent": -10.0,
                "liquidation_price": 50000,
                "notes": "Sample market alert created by Cyclone",
                "description": "Cyclone test alert",
                "position_reference_id": None,
                "evaluated_value": 59000,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            success = self.data_locker.create_alert(dummy_alert)
            if success:
                log.success("Market alert created successfully.", source="Cyclone")
            else:
                log.warning("Market alert creation failed.", source="Cyclone")
        except Exception as e:
            log.error(f"Error creating market alert: {e}", source="Cyclone")

    async def run_clear_all_data(self):
        log.warning("⚠️ Starting Clear All Data", source="Cyclone")
        try:
            await asyncio.to_thread(self._clear_all_data_core)
            log.success("All alerts, prices, and positions have been deleted.", source="Cyclone")
        except Exception as e:
            log.error(f"Clear All Data failed: {e}", source="Cyclone")

    def _clear_all_data_core(self):
        tables = ["alerts", "prices", "positions"]
        for table in tables:
            try:
                cursor = self.data_locker.db.get_cursor()
                cursor.execute(f"DELETE FROM {table}")
                self.data_locker.db.commit()
                cursor.close()
                log.success(f"✅ Cleared all rows from `{table}`", source="Cyclone")
            except Exception as e:
                log.error(f"❌ Failed to clear `{table}`: {e}", source="Cyclone")

    def run_debug_position_update(self):
        print("💡 DEBUG: calling CyclonePositionService.update_positions_from_jupiter()")
        self.position_runner.update_positions_from_jupiter()

    async def run_cycle(self, steps=None):
        available_steps = {
            "clear_all_data": self.run_clear_all_data,
            "market": self.run_market_updates,
            "position": self.run_composite_position_pipeline,
            "cleanse_ids": self.alert_runner.clear_stale_alerts,
            "enrich positions": self.position_runner.enrich_positions,
            "enrich alerts": self.alert_runner.enrich_all_alerts,
            "create_market_alerts": self.run_create_market_alerts,
            "create_portfolio_alerts": self.portfolio_runner.create_portfolio_alerts,
            "create_position_alerts": self.position_runner.create_position_alerts,
            "update_evaluated_value": self.alert_runner.update_evaluated_values,
            "alert": self.alert_runner.run_alert_updates
        }

        default_order = [
            "clear_all_data", "market", "position", "cleanse_ids",
            "enrich positions", "enrich alerts", "create_market_alerts",
            "create_position_alerts", "create_portfolio_alerts",
            "update_evaluated_value", "alert", "link_hedges", "update_hedges"
        ]

        run_list = steps or default_order
        for step in run_list:
            log.info(f"🧩 Executing step: {step}", source="Cyclone")
            if step in available_steps:
                try:
                    result = available_steps[step]
                    if asyncio.iscoroutinefunction(result):
                        await result()
                    else:
                        result()
                except Exception as e:
                    log.error(f"❌ Step '{step}' failed: {e}", source="Cyclone")
            else:
                log.warning(f"Unknown step: {step}", source="Cyclone")

    def run_delete_all_data(self):
        log.warning("⚠️ Deletion requested via legacy method (run_delete_all_data)", source="Cyclone")
        asyncio.run(self.run_clear_all_data())


if __name__ == "__main__":
    configure_cyclone_console_log()

    from cyclone.cyclone_console_service import CycloneConsoleService
    cyclone = Cyclone(poll_interval=60)
    helper = CycloneConsoleService(cyclone)
    helper.run()
