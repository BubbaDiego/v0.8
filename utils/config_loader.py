import json
from pathlib import Path
from utils.console_logger import ConsoleLogger as log
import os
import sys

def load_config(config_path: str) -> dict:
    try:
        if not os.path.exists(config_path):
            if "pytest" in sys.modules:
                # If running tests, don't warn about missing config
                return {}
            else:
                from utils.console_logger import ConsoleLogger as log
                log.warning(f"Configuration file not found: {config_path}", source="ConfigLoader")
                return {}
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        from utils.console_logger import ConsoleLogger as log
        log.error(f"Failed to load config: {e}", source="ConfigLoader")
        return {}

