import json
from pathlib import Path
from utils.console_logger import ConsoleLogger as log
import os
import sys

from config.config_constants import ALERT_LIMITS_PATH

def load_config(filename):
    full_path = os.path.abspath(filename)
    if os.path.exists(full_path):
        print(f"✅ [ConfigLoader] Loading config from: {full_path}")
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"⚠️ [ConfigLoader] Not found: {full_path}, trying fallback: {ALERT_LIMITS_PATH}")
    if os.path.exists(ALERT_LIMITS_PATH):
        with open(ALERT_LIMITS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"❌ [ConfigLoader] ALERT_LIMITS_PATH also missing: {ALERT_LIMITS_PATH}")
    return {}



