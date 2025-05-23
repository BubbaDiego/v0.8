import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from flask import current_app
from core.logging import log

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
                        "server": os.getenv("SMTP_SERVER"),
                        "port": int(os.getenv("SMTP_PORT", "0")) if os.getenv("SMTP_PORT") else None,
                        "username": os.getenv("SMTP_USERNAME"),
                        "password": os.getenv("SMTP_PASSWORD"),
                        "default_recipient": os.getenv("SMTP_DEFAULT_RECIPIENT"),
                    },
                }

            # Fallback for Twilio if missing/empty
            if name == "twilio" and not provider:
                provider = {
                    "enabled": True,
                    "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
                    "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
                    "flow_sid": os.getenv("TWILIO_FLOW_SID"),
                    "default_to_phone": os.getenv("TWILIO_TO_PHONE"),
                    "default_from_phone": os.getenv("TWILIO_FROM_PHONE"),
                }
            return provider
        except Exception as e:
            log.error(f"Failed to load provider config for '{name}': {e}", source="XComConfigService")
            return {}

