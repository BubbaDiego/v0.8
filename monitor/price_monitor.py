import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

import logging
from datetime import datetime, timezone
import requests

from monitor.base_monitor import BaseMonitor
from data.data_locker import DataLocker
from utils.console_logger import ConsoleLogger as log
from core.core_imports import DB_PATH


class PriceFetcher:
    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

    def __init__(self):
        self.params = {
            "ids": "bitcoin,ethereum,solana",
            "vs_currencies": "usd"
        }

    def get_prices(self):
        log.info("🔍 Fetching prices from CoinGecko...", source="PriceFetcher")
        try:
            resp = requests.get(self.COINGECKO_URL, params=self.params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            log.success("✅ Price fetch successful", source="PriceFetcher")
            return {
                "BTC": data.get("bitcoin", {}).get("usd"),
                "ETH": data.get("ethereum", {}).get("usd"),
                "SOL": data.get("solana", {}).get("usd"),
            }
        except Exception as e:
            log.error(f"❌ Error fetching prices: {e}", source="PriceFetcher")
            return {}


class PriceMonitor(BaseMonitor):
    def __init__(self, timer_config_path=None, ledger_filename=None):
        super().__init__(
            name="price_monitor",  # ✅ ensure lowercase snake_case
            timer_config_path=timer_config_path,
            ledger_filename=ledger_filename or "price_ledger.json"
        )
        self.data_locker = DataLocker(DB_PATH)
        self.fetcher = PriceFetcher()

    def _do_work(self):
        log.banner("📈 Price Monitor Cycle Start")

        prices = self.fetcher.get_prices()
        count = 0

        log.debug("Fetched raw price data", source=self.name, payload=prices)

        for symbol, price in prices.items():
            if price is not None:
                self.data_locker.insert_or_update_price(symbol, price, "PriceMonitor")
                log.info(f"💾 Saved {symbol} = ${price:.2f}", source=self.name)
                count += 1
            else:
                log.warning(f"⚠️ No price for {symbol}", source=self.name)

        now = datetime.now(timezone.utc)

        self.data_locker.set_last_update_times({
            "last_update_time_positions": None,
            "last_update_positions_source": None,
            "last_update_time_prices": now.isoformat(),
            "last_update_prices_source": "PriceMonitor",
            "last_update_time_jupiter": now.isoformat(),
            "last_update_jupiter_source": "PriceMonitor"
        })

        # ✅ Confirm insertion and echo debug
        log.debug("🧠 About to insert ledger entry...", source=self.name)
        self.data_locker.ledger.insert_ledger_entry(
            monitor_name=self.name,
            status="Success" if count > 0 else "NoPrices",
            metadata={"fetched_count": count}
        )

        log.success(f"✅ Price cycle complete — {count} prices updated", source=self.name)
        return {"fetched_count": count}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pm = PriceMonitor()
    try:
        pm.run_cycle()
        log.success("💥 PriceMonitor CLI run complete", source="PriceMonitor")
    except Exception as e:
        log.error(f"🔥 PriceMonitor error: {e}", source="PriceMonitor")
