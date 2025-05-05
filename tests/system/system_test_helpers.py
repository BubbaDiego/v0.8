import json
import os

def create_temp_alert_limits_json(filepath="alert_limitsz.json"):
    """
    Create a dummy alert_limitsz.json if it doesn't exist.
    """
    if os.path.exists(filepath):
        return  # ✅ Already exists, do nothing

    dummy_config = {
        "alert_cooldown_seconds": 900,
        "global_alert_config": {
            "max_alerts": 1000
        },
        "alert_ranges": {
            "PriceThreshold": {
                "LOW": 5000,
                "MEDIUM": 10000,
                "HIGH": 20000
            }
        }
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(dummy_config, f, indent=4)
