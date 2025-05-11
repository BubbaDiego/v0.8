import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
from datetime import datetime
from uuid import uuid4
from monitor.price_monitor import PriceMonitor
from alerts.alert_core import AlertCore #alert_service_manager import AlertServiceManager
from data.data_locker import DataLocker
from core.constants import DB_PATH
from core.logging import log
from core.constants import DB_PATH, ALERT_LIMITS_PATH
from config.config_loader import load_config

# Cores and Services
from alerts.alert_core import AlertCore
from positions.position_core import PositionCore
from cyclone.cyclone_maintenance_service import CycloneMaintenanceService
from cyclone.cyclone_wallet_service import CycloneWalletService


global_data_locker = DataLocker(str(DB_PATH))  # There can be only one
logging.basicConfig(level=logging.DEBUG)

def configure_cyclone_console_log():
    """
    🧠 Centralized Cyclone Console Log Config
    Enables all core modules for debugging.
    """
    log.silence_module("werkzeug")
    log.silence_module("fuzzy_wuzzy")

    # Hijack asyncio logger early
    log.hijack_logger("asyncio")

    # Optionally silence it altogether
    log.silence_module("asyncio")

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

        self.data_locker = global_data_locker
        self.price_monitor = PriceMonitor()
        self.config = load_config(str(ALERT_LIMITS_PATH))

        self.position_core = PositionCore(self.data_locker)
        self.alert_core = AlertCore(self.data_locker, lambda: self.config)
        self.wallet_service = CycloneWalletService(self.data_locker)
        self.maintenance_service = CycloneMaintenanceService(self.data_locker)

        log.banner("🌀  🌪️ CYCLONE ENGINE STARTUP 🌪️ 🌀")

    async def run_market_updates(self):
        log.info("Starting Market Updates", source="Cyclone")
        try:
            await self.price_monitor.update_prices(source="Market Updates")
            log.success("📈 Prices updated successfully ✅", source="Cyclone")
        except Exception as e:
            log.error(f"📉Market Updates failed 💥💥💥💥💥💥: {e}", source="Cyclone")

    async def run_composite_position_pipeline(self):
        await asyncio.to_thread(self.position_core.update_positions_from_jupiter)

    async def run_create_market_alerts(self):
        await self.alert_service.create_market_alerts()

    async def run_clear_all_data(self):
        log.warning("⚠️ Starting Clear All Data", source="Cyclone")
        try:
            await asyncio.to_thread(self._clear_all_data_core)
            log.success("All alerts, prices, and positions have been deleted.", source="Cyclone")
        except Exception as e:
            log.error(f"Clear All Data failed: {e}", source="Cyclone")

    def run_debug_position_update(self):
        print("💡 DEBUG: calling CyclonePositionService.update_positions_from_jupiter()")
        self.position_core.update_positions_from_jupiter()

    async def run_cycle(self, steps=None):
        available_steps = {
           # "clear_all_data": self.run_clear_all_data,
            "market_updates": self.run_market_updates,
            "check_jupiter_for_updates": self.run_check_jupiter_for_updates,
            "enrich_positions": self.run_enrich_positions,
            "enrich_alerts": self.run_alert_enrichment,
            "update_evaluated_value": self.run_update_evaluated_value,
            "create_portfolio_alerts": self.run_create_portfolio_alerts,
            "create_position_alerts": self.run_create_position_alerts,
            "create_global_alerts": self.run_create_global_alerts,
            "evaluate_alerts": self.run_alert_evaluation,
            "cleanse_ids": self.run_cleanse_ids,
            "link_hedges": self.run_link_hedges,

        }

        steps = steps or list(available_steps.keys())

        for step in steps:
            if step not in available_steps:
                log.warning(f"⚠️ Unknown step: '{step}'", source="Cyclone")
                continue
            log.info(f"▶️ Running step: {step}", source="Cyclone")
            await available_steps[step]()

    def run_delete_all_data(self):
        log.warning("⚠️ Deletion requested via legacy method (run_delete_all_data)", source="Cyclone")
        asyncio.run(self.run_clear_all_data())

    async def run_create_position_alerts(self):
        await self.position_core.create_position_alerts()

    async def run_create_portfolio_alerts(self):
        await self.portfolio_runner.create_portfolio_alerts()

    async def run_link_hedges(self):
        self.position_core.link_hedges()

    async def run_update_hedges(self):
        await self.position_core.update_hedges()

    async def run_alert_evaluation(self):
        await self.alert_core.run_alert_evaluation()

    async def run_create_position_alerts(self):
        self.alert_core.create_position_alerts()

    async def run_create_portfolio_alerts(self):
        self.alert_core.create_portfolio_alerts()

    async def run_create_global_alerts(self):
        #await self.alert_core.create_global_alerts()
        log.success("Global Alerts PlLace Holder", source="Cyclone")

    def clear_alerts_backend(self):
        self.data_locker.alerts.clear_all_alerts()
        log.success("🧹 All alerts cleared from backend", source="Cyclone")

    async def run_cleanse_ids(self):
        log.info("🧹 Running cleanse_ids: clearing stale alerts", source="Cyclone")
        self.alert_core.clear_stale_alerts()
        log.success("✅ Alert IDs cleansed", source="Cyclone")

    async def run_enrich_positions(self):
        await self.position_core.enrich_positions()
        log.success("✅ Position enrichment complete", source="Cyclone")

    async def run_alert_enrichment(self):
        await self.alert_core.enrich_all_alerts()
        log.success("✅ Alert enrichment complete", source="Cyclone")

    async def run_update_evaluated_value(self):
        await self.alert_core.update_evaluated_values()
        log.success("✅ Evaluated alert values updated", source="Cyclone")

    def clear_prices_backend(self):
        self.sys.clear_prices()

    def clear_wallets_backend(self):
        self.sys.clear_wallets()

    def clear_alerts_backend(self):
        self.sys.clear_alerts()

    def clear_positions_backend(self):
        self.sys.clear_positions()

    def _clear_all_data_core(self):
        self.sys.clear_all_tables()

    # ⚙️ Corrected clear helpers
    def clear_prices_backend(self):
        self.maintenance_service.clear_prices()

    def clear_wallets_backend(self):
        self.maintenance_service.clear_wallets()

    def clear_alerts_backend(self):
        self.maintenance_service.clear_alerts()

    def clear_positions_backend(self):
        self.maintenance_service.clear_positions()

    def _clear_all_data_core(self):
        self.maintenance_service.clear_all_tables()

    async def run_position_updates(self):
        await asyncio.to_thread(self.position_core.update_positions_from_jupiter)

    # -------------------------------
        # 🔹 Step 1: Check Jupiter Updates
        # -------------------------------
    async def run_check_jupiter_for_updates(self):
        log.info("🚀 Checking Jupiter for Position Updates...", "Cyclone")
        self.position_core.update_positions_from_jupiter()
        log.success("✅ Jupiter sync complete.", "Cyclone")

    # -------------------------------
    # 🔹 Step 2: Enrich Positions
    # -------------------------------
    async def enrich_positions(self):
        log.info("🚀 Enriching All Positions via PositionCore...", "Cyclone")
        await self.position_core.enrich_positions()
        log.success("✅ Position enrichment complete.", "Cyclone")
