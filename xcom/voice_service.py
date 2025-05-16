# xcom/voice_service.py
import sys
import requests
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from twilio.rest import Client
from utils.console_logger import ConsoleLogger as log

from flask import current_app


class VoiceService:
    def __init__(self, config: dict):
        self.config = config

    import requests
    from utils.console_logger import ConsoleLogger as log
    from flask import current_app

    def call(self, recipient: str, message: str) -> bool:
        try:
            account_sid = self.config.get("account_sid")
            auth_token = self.config.get("auth_token")
            flow_sid = self.config.get("flow_sid")
            from_phone = self.config.get("default_from_phone")
            to_phone = recipient or self.config.get("default_to_phone")

            if not all([account_sid, auth_token, flow_sid, from_phone, to_phone]):
                raise ValueError("Missing required Twilio voice config")

            url = f"https://studio.twilio.com/v2/Flows/{flow_sid}/Executions"
            payload = {
                "To": to_phone,
                "From": from_phone
            }

            headers = {"Accept-Charset": "utf-8"}

            response = requests.post(
                url,
                data=payload,
                headers=headers,
                auth=(account_sid, auth_token)
            )

            # 🔍 Full verbose logging
            log.info("🔍 Twilio Voice request debug", payload={
                "url": url,
                "payload": payload,
                "auth_sid": account_sid,
                "status_code": response.status_code,
                "response_text": response.text
            }, source="VoiceService")

            if response.status_code == 201:
                return True

            # If we get 401 or other
            if response.status_code == 401:
                if hasattr(current_app, "system_core"):
                    current_app.system_core.death({
                        "message": "Twilio Voice Call failed: 401 Unauthorized",
                        "payload": {
                            "status_code": 401,
                            "provider": "twilio",
                            "flow_sid": flow_sid,
                            "to": to_phone,
                            "from": from_phone,
                            "response_text": response.text
                        },
                        "level": "HIGH"
                    })

            return False

        except Exception as e:
            log.error(f"Voice call failed: {e}", source="VoiceService")
            return False

