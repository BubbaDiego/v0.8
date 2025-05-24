import json
import os
from pathlib import Path
from core.core_imports import ALERT_LIMITS_PATH, log


def _deep_merge(base: dict, overrides: dict) -> dict:
    """Recursively merge ``overrides`` into ``base`` returning a new dict."""
    result = dict(base)
    for key, value in overrides.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(filename=None):
    """
    Always loads from ALERT_LIMITS_PATH unless explicitly overridden with a full absolute path.
    """
    if not filename or Path(filename).name == "alert_limitsz.json":
        filename = str(ALERT_LIMITS_PATH)

    if not os.path.isabs(filename):
        filename = os.path.abspath(filename)

    if os.path.exists(filename):
        log.info(f"✅ [ConfigLoader] Loading config from: {filename}", source="ConfigLoader")
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    log.error(f"❌ [ConfigLoader] Config not found at: {filename}", source="ConfigLoader")
    return {}


def update_config(new_config: dict, filename: str | None = None) -> dict:
    """Merge ``new_config`` into the existing config and persist the result."""
    filename = str(ALERT_LIMITS_PATH) if not filename or Path(filename).name == "alert_limitsz.json" else os.path.abspath(filename)

    current = load_config(filename)
    merged = _deep_merge(current, new_config)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
    return merged




