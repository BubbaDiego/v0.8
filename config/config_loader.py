import json
from pathlib import Path
from utils.console_logger import ConsoleLogger as log
import os
import sys

from config.config_constants import ALERT_LIMITS_PATH

import json
import os
from pathlib import Path
from config.config_constants import ALERT_LIMITS_PATH
from utils.console_logger import ConsoleLogger as log

def load_config(filename=None):
    """
    Always loads from ALERT_LIMITS_PATH unless explicitly overridden with a full absolute path.
    """
    if not filename or Path(filename).name == "alert_limits.json":
        filename = str(ALERT_LIMITS_PATH)

    if not os.path.isabs(filename):
        filename = os.path.abspath(filename)

    if os.path.exists(filename):
        log.info(f"✅ [ConfigLoader] Loading config from: {filename}", source="ConfigLoader")
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    log.error(f"❌ [ConfigLoader] Config not found at: {filename}", source="ConfigLoader")
    return {}




