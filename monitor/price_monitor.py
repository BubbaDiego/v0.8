#!/usr/bin/env python3
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict

import requests
from monitor.monitor_utils import BaseMonitor
from data.data_locker import DataLocker

from core.constants import DB_PATH
from utils.console_logger import ConsoleLogger as log


class PriceFetcher:
    """
    Lightweight CoinGecko price fetcher for BTC, ETH, SOL.
    """
    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

    def __init__(self):
        self.params = {
            "ids": "bitcoin,ethereum,solana",
            "vs_currencies": "usd"
        }

    def get_prices(self) -> Dict[str, float]:
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
    """
    Standalone price monitor service.
    Periodically fetches market prices, stores in DB, logs to ledger, and logs to console.
    """

    def __init__(self, timer_config_path: str = None, ledger_filename: str = None):
        super().__init__(
            name="price_monitor",
            timer_config_path=timer_config_path,
            ledger_filename=ledger_filename or "price_ledger.json"
        )
        self.data_locker = DataLocker(str(DB_PATH))
        self.fetcher = PriceFetcher()

    def _do_work(self) -> dict:
        """
        Fetch prices, update database, log ledger and console.
        Returns metadata.
        """
        log.banner("📈 Price Monitor Cycle Start")
        prices = self.fetcher.get_prices()
        count = 0

        log.debug("Fetched raw price data", source="PriceMonitor", payload=prices)

        for symbol, price in prices.items():
            if price is not None:
                self.data_locker.insert_or_update_price(symbol, price, "Fetched")
                log.info(f"💾 Saved {symbol} = ${price:.2f}", source="PriceMonitor")
                count += 1
            else:
                log.warning(f"⚠️ No price returned for {symbol}", source="PriceMonitor")

        now = datetime.now(timezone.utc)
        self.data_locker.set_last_update_times(prices_dt=now, prices_source="PriceMonitor")

        ledger_entry = {
            "timestamp": now.isoformat(),
            "component": self.name,
            "operation": "price_update",
            "status": "Success" if count > 0 else "NoPrices",
            "metadata": {"fetched_count": count}
        }
        self.ledger_writer.write(self.ledger_file, ledger_entry)

        log.success(f"✅ Price cycle complete — {count} prices updated", source="PriceMonitor")
        return {"loop_counter": count}

    async def update_prices(self, source: str = "Manual") -> dict:
        """
        Cyclone-compatible async price update trigger.
        """
        log.info(f"⏳ Async price update triggered by {source}", source="PriceMonitor")
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(None, self._do_work)
        log.info("✅ Async price update complete", source="PriceMonitor")
        return metadata


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pm = PriceMonitor(timer_config_path=os.getenv("TIMER_CONFIG_PATH"))
    try:
        pm.run_cycle()
        log.success("💥 PriceMonitor CLI cycle complete", source="PriceMonitor")
    except Exception as e:
        log.error(f"🔥 PriceMonitor error: {e}", source="PriceMonitor")
