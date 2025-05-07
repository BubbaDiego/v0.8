# core/logging.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.console_logger import ConsoleLogger as log

def configure_cyclone_console_log():
    """
    🧠 Cyclone Logging Configuration

    This sets up logging behavior across Cyclone services:
    - Silences noisy or irrelevant modules
    - Assigns core components into a logging group
    - Emits initial logger status
    """
    # 🔇 Silence noisy logs
    log.silence_module("werkzeug")
    log.silence_module("fuzzy_wuzzy")
    log.silence_module("flask")
    log.silence_module("calc_services")
   # log.silence_prefix("calculate")

    # 🧠 Grouping for Cyclone core services
    log.assign_group("cyclone_core", [
        "cyclone_engine",
        "Cyclone",
        "CycloneHedgeService",
        "CyclonePortfolioService",
        "CycloneAlertService",
        "CyclonePositionService"
    ])
    log.enable_group("cyclone_core")

    # 📊 Show current log state
    log.init_status()
