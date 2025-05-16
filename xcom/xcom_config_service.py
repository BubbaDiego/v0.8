from flask import current_app
from utils.console_logger import ConsoleLogger as log

class XComConfigService:
    def __init__(self, dl_sys):
        self.dl_sys = dl_sys  # Not used directly anymore

    def get_provider(self, name: str) -> dict:
        try:
            # ✅ Use DataLocker directly from Flask app context
            locker = getattr(current_app, "data_locker", None)
            if not locker or not hasattr(locker, "system"):
                raise Exception("data_locker.system not available")

            # ✅ Safely access stored XCom config (flat model)
            config = locker.system.get_var("xcom_providers") or {}
            return config.get(name, {})

        except Exception as e:
            log.error(f"Failed to load provider config for '{name}': {e}", source="XComConfigService")
            return {}
