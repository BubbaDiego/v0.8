import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
import time
from datetime import datetime, timezone
from cyclone.cyclone_engine import Cyclone    # Adjust import as needed

logging.basicConfig(level=logging.INFO)

def heartbeat(loop_counter: int):
    timestamp = datetime.now(timezone.utc).isoformat()
    logging.info("❤️ SonicMonitor heartbeat #%d at %s", loop_counter, timestamp)

async def sonic_cycle(loop_counter: int, cyclone: Cyclone):
    logging.info("🔄 SonicMonitor cycle #%d starting", loop_counter)
    await cyclone.run_cycle()    # <--- THIS RUNS YOUR FULL BACKEND UPDATE
    heartbeat(loop_counter)
    logging.info("✅ SonicMonitor cycle #%d complete", loop_counter)

def main():
    loop_counter = 0
    interval = 60  # or load from config

    cyclone = Cyclone()  # Set poll_interval if needed

    loop = asyncio.get_event_loop()
    try:
        while True:
            loop_counter += 1
            loop.run_until_complete(sonic_cycle(loop_counter, cyclone))
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("SonicMonitor terminated by user.")

if __name__ == "__main__":
    main()
