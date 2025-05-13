# core/logging.py

import sys
import os
from utils.console_logger import ConsoleLogger as log  # ✅ DEFINE IT HERE

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def configure_console_log():
    """
    🧠 Cyclone Logging Configuration
    """
    log.hijack_logger("werkzeug")
  #  log.silence_module("werkzeug")
    #log.silence_module("fuzzy_wuzzy")
    #log.silence_module("flask")
    log.silence_module("calc_services")

    log.assign_group("cyclone_core", [
        "cyclone_engine",
        "Cyclone",
        "CycloneHedgeService",
        "CyclonePortfolioService",
        "CycloneAlertService",
        "CyclonePositionService"
    ])
    log.enable_group("cyclone_core")
    log.init_status()
