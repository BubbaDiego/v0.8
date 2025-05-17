import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import current_app
from utils.console_logger import ConsoleLogger as log

class XComConfigService:
    def __init__(self, dl_sys):
        self.dl_sys = dl_sys  # Not used directly anymore

    def get_provider(self, name: str) -> dict:
        try:
            locker = getattr(current_app, "data_locker", None)
            if not locker or not hasattr(locker, "system"):
                raise Exception("data_locker.system not available")
            config = locker.system.get_var("xcom_providers") or {}
            provider = config.get(name, {})
            # Fallback for email if missing/empty
            if name == "email" and (not provider or not provider.get("smtp")):
                provider = {
                    "enabled": True,
                    "smtp": {
                        "server": "smtp.gmail.com",
                        "port": 587,
                        "username": "bubba.diego@gmail.com",
                        "password": "pzix taan afbe igxb",
                        "default_recipient": "bubba.diego@gmail.com"
                    }
                }
            return provider
        except Exception as e:
            log.error(f"Failed to load provider config for '{name}': {e}", source="XComConfigService")
            return {}

