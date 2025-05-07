import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from data.data_locker import DataLocker
from monitor.price_monitor import PriceMonitor
from monitor.monitor_utils import LedgerWriter
from alerts.alert_utils import log_alert_summary
from alerts.alert_service_manager import AlertServiceManager
from utils.console_logger import ConsoleLogger as log
from config.config_loader import load_config
from config.config_constants import ALERT_LIMITS_PATH

from cyclone.cyclone_position_service import CyclonePositionService
from cyclone.cyclone_portfolio_service import CyclonePortfolioService
from cyclone.cyclone_alert_service import CycloneAlertService
from cyclone.cyclone_hedge_service import CycloneHedgeService


class Cyclone:
    def __init__(self, poll_interval=60):
        self.logger = logging.getLogger("Cyclone")
        self.poll_interval = poll_interval
        self.logger.setLevel(logging.DEBUG)

        self.data_locker = DataLocker.get_instance()
        self.price_monitor = PriceMonitor()
        self.alert_service = AlertServiceManager.get_instance()
        self.config = load_config(str(ALERT_LIMITS_PATH))

        self.portfolio_runner = CyclonePortfolioService()
        self.position_runner = CyclonePositionService()
        self.alert_runner = CycloneAlertService()
        self.hedge_runner = CycloneHedgeService()

        log.banner("🌀  🌪️ CYCLONE ENGINE STARTUP 🌪️ 🌀")
        log.success("Cyclone orchestrator initialized.", source="Cyclone")

    async def run_market_updates(self):
        log.info("Starting Market Updates", source="Cyclone")
        try:
            await self.price_monitor.update_prices(source="Market Updates")
            log.success("Prices updated successfully", source="Cyclone")
        except Exception as e:
            log.error(f"Market Updates failed: {e}", source="Cyclone")

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
            log.success("Market alert created successfully." if success else "Failed to create market alert.", source="Cyclone")
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
        try:
            for table in ["alerts", "prices", "positions"]:
                cursor = self.data_locker.conn.cursor()
                cursor.execute(f"DELETE FROM {table}")
                self.data_locker.conn.commit()
                cursor.close()
                log.info(f"Cleared {table}", source="Cyclone")
        except Exception as e:
            log.error(f"Error clearing data: {e}", source="Cyclone")

    async def run_cycle(self, steps=None):
        """
        Master run_cycle method to run modular steps across services.
        """
        available_steps = {
            "clear_all_data": self.run_clear_all_data,
            "market": self.run_market_updates,
            "position": self.position_runner.update_positions_from_jupiter,
            "cleanse_ids": self.alert_runner.clear_stale_alerts,
            "link_hedges": self.hedge_runner.link_hedges,
            "update_hedges": self.hedge_runner.update_hedges,
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
            if step in available_steps:
                await available_steps[step]()
            else:
                log.warning(f"Unknown step: {step}", source="Cyclone")

    def run_delete_all_data(self):
        """
        ⚠️ Compatibility alias for legacy menu option.
        Calls run_clear_all_data internally.
        """
        log.warning("⚠️ Deletion requested via legacy method (run_delete_all_data)", source="Cyclone")
        asyncio.run(self.run_clear_all_data())


if __name__ == "__main__":
    from cyclone_console_helper import CycloneConsoleHelper

    log.banner("🌀 Cyclone CLI Console Activated 🌀")
    cyclone = Cyclone(poll_interval=60)
    helper = CycloneConsoleHelper(cyclone)
    helper.run()
2

