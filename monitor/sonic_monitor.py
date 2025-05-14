# monitor/monitors/sonic_monitor.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import logging
import asyncio
from datetime import datetime, timezone
from monitor.monitor_utils import load_timer_config, update_timer_config
from monitor.monitor_core import MonitorCore
from monitor.monitor_registry import MonitorRegistry
from monitor.price_monitor import PriceMonitor
from monitor.operations_monitor import OperationsMonitor

logging.basicConfig(level=logging.INFO)

def heartbeat(loop_counter: int):
    timestamp = datetime.now(timezone.utc).isoformat()
    cfg = load_timer_config()
    cfg["sonic_loop_start_time"] = timestamp
    update_timer_config(cfg)
    logging.info("❤️ SonicMonitor heartbeat #%d at %s", loop_counter, timestamp)

async def run_cycle(loop_counter: int, core: MonitorCore):
    logging.info("🔄 SonicMonitor cycle #%d starting", loop_counter)
    core.run_all()
    heartbeat(loop_counter)
    logging.info("✅ SonicMonitor cycle #%d complete", loop_counter)

def main():
    loop_counter = 0
    interval = load_timer_config().get("sonic_loop_interval", 60)

    # Setup registry + monitors
    registry = MonitorRegistry()
    registry.register("price_monitor", PriceMonitor())
    registry.register("operations_monitor", OperationsMonitor())
    core = MonitorCore(registry)

    loop = asyncio.get_event_loop()

    try:
        while True:
            loop_counter += 1
            loop.run_until_complete(run_cycle(loop_counter, core))
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("SonicMonitor terminated by user.")

if __name__ == "__main__":
    main()
