import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from monitor.base_monitor import BaseMonitor
from data.data_locker import DataLocker
from monitor.monitor_service import MonitorService
from core.core_imports import DB_PATH
from datetime import datetime, timezone
from utils.console_logger import ConsoleLogger as log


class PriceMonitor(BaseMonitor):
    """
    Fetches prices from external APIs and stores them in DB.
    Uses CoinGecko via MonitorService.
    """

    def __init__(self):
        super().__init__(
            name="price_monitor",
            ledger_filename="price_ledger.json",  # still optional, safe to retain
            timer_config_path=None  # leave in for compatibility
        )
        self.dl = DataLocker(str(DB_PATH))
        self.service = MonitorService()

    def _do_work(self):
        log.info("🔍 Fetching prices from CoinGecko...", source="PriceFetcher")
        prices = self.service.fetch_prices()

        if not prices:
            log.warning("⚠️ No prices fetched", source="PriceFetcher")
            return {
                "fetched_count": 0,
                "error": "No prices returned",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        for asset, price in prices.items():
            self.dl.insert_or_update_price(asset, price, source=self.name)
            log.info(f"💾 Saved {asset} = ${price:,.2f}", source=self.name)

        log.success("✅ Price fetch successful", source="PriceFetcher")

        return {
            "fetched_count": len(prices),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
