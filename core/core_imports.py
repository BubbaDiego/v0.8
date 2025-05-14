# core/core_imports.py
"""
Centralized import hub for high-usage components in the Sonic Dashboard.
Use this instead of importing from `core/__init__.py`.
"""
import os

# Absolute path to /data/mother_brain.db with env override
DB_PATH = os.getenv(
    "DB_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "mother_brain.db"))
)

from core.logging import log, configure_console_log
#from core.locker_factory import get_locker
from core.constants import DB_PATH, CONFIG_PATH, BASE_DIR, ALERT_LIMITS_PATH
from utils.db_retry import retry_on_locked
#from utils.json_manager import JsonManager
