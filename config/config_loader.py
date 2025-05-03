import json
from pathlib import Path
from utils.console_logger import ConsoleLogger as log
import os
import sys

from config.config_constants import ALERT_LIMITS_PATH

def load_config(filename=None):
    """
    Load alert_limits.json from configured ALERT_LIMITS_PATH by default.
    """
    if not filename:
        filename = ALERT_LIMITS_PATH
    elif not os.path.isabs(filename):
        filename = os.path.abspath(filename)

    if os.path.exists(filename):
        print(f"✅ [ConfigLoader] Loading config from: {filename}")
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"❌ [ConfigLoader] Config not found at: {filename}")
    return {}



